"""Daily freshness check for the published step data, with Telegram alerting.

The recurring failure mode this exists for: the Google Health OAuth token expires
or gets revoked, `run_daily()` / `run_intraday()` crash inside cron, and nothing
says so. The dashboard just quietly freezes on stale numbers.

This checks the *published* data, not the API: it reads the public bucket over
plain HTTPS, so it needs no Google credentials, never touches the Google Health
API, and is safe to run from any machine (unlike main.py, see CLAUDE.md).

    poetry run python watchdog.py               # check, alert if broken
    poetry run python watchdog.py --test-alert  # send a test message and exit

Exits 1 when a check fails (so cron mail / logs see it too).

Blind spot: this runs on the same Pi as the cron jobs it watches, so it stays
silent if the Pi itself is down. It catches the token failure, not a dead Pi.
"""

from pathlib import Path
from dotenv import load_dotenv
import datetime
import argparse
import os
import re
import sys
import requests

ROOT_DIR = Path(__file__).parent

load_dotenv(ROOT_DIR / ".env")

GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")
PUBLIC_BUCKET_BASE_URL = "https://storage.googleapis.com"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HTTP_TIMEOUT_SECONDS = 20

# today.json is refreshed hourly between 08:00 and 23:00. Anything older than
# yesterday means the intraday job has been down for at least a full day.
TODAY_JSON_MAX_AGE_DAYS = 1

# Cron logs to attach to an alert, so the actual error travels with the message
# instead of the message telling you to go read a file.
LOG_FILES = [ROOT_DIR / "cron.log", ROOT_DIR / "intraday.log"]
LOG_TAIL_LINES = 12
# Read at most this much from the end of a log; intraday.log grows unbounded.
LOG_TAIL_MAX_BYTES = 64 * 1024
# Telegram rejects messages over 4096 characters.
TELEGRAM_MAX_CHARS = 4096
# Telegram guesses a language for an unlabelled <pre> block and syntax-highlights
# it, so a traceback in cron.log renders as coloured Python while intraday.log
# stays grey. Naming the language keeps every log block uniformly plain.
LOG_CODE_LANGUAGE = "plaintext"


def public_url(blob_name):
    return f"{PUBLIC_BUCKET_BASE_URL}/{GCP_BUCKET_NAME}/{blob_name}"


def fetch_json(blob_name):
    """GET a blob from the public bucket. cache-busted so the CDN can't lie to us."""
    response = requests.get(
        public_url(blob_name),
        params={"_": datetime.datetime.now().timestamp()},
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def latest_record_date(records):
    """Newest `date` in a data.json-shaped list, as a date. None if empty."""
    dates = [
        datetime.date.fromisoformat(r["date"]) for r in records if r.get("date")
    ]
    return max(dates) if dates else None


def check_yesterday(records, today):
    """The core check: data.json must contain a record for yesterday.

    Returns a problem string, or None when everything is fine.
    """
    yesterday = today - datetime.timedelta(days=1)
    latest = latest_record_date(records)

    if latest is None:
        return "data.json has no records at all."
    if latest < yesterday:
        days_behind = (yesterday - latest).days
        return (
            f"data.json has no record for yesterday ({yesterday}). "
            f"Newest record is {latest}, {days_behind} day(s) behind. "
            f"The daily job has not landed data."
        )
    return None


def check_today_json(record, today):
    """Secondary check: today.json should not be older than yesterday.

    Catches the same token failure within hours instead of waiting for the next
    daily run, because the intraday job runs hourly.
    """
    date_str = (record or {}).get("date")
    if not date_str:
        return "today.json has no date field."

    date = datetime.date.fromisoformat(date_str)
    age_days = (today - date).days
    if age_days > TODAY_JSON_MAX_AGE_DAYS:
        return (
            f"today.json is stale: dated {date}, {age_days} days old. "
            f"The hourly intraday job has stopped."
        )
    return None


def run_checks(today=None):
    """Run every check. Returns a list of problem strings (empty = healthy)."""
    today = today or datetime.date.today()
    problems = []

    try:
        problem = check_yesterday(fetch_json("data.json"), today)
        if problem:
            problems.append(problem)
    except Exception as e:
        problems.append(f"Could not read data.json from the bucket: {e}")

    try:
        problem = check_today_json(fetch_json("today.json"), today)
        if problem:
            problems.append(problem)
    except Exception as e:
        problems.append(f"Could not read today.json from the bucket: {e}")

    return problems


def _post_message(text, parse_mode=None):
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    return requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json=payload,
        timeout=HTTP_TIMEOUT_SECONDS,
    )


def send_telegram(text, plain_fallback=None):
    """Post a message via the Telegram bot API. Returns True when it went out.

    Sent with parse_mode=HTML so the log tails render as monospace blocks. If
    Telegram rejects the markup, the alert is retried unformatted: an alert that
    arrives ugly beats an alert that never arrives.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(
            "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set in .env, "
            "alert not sent, printing instead:"
        )
        print(plain_fallback or text)
        return False

    response = _post_message(text, parse_mode="HTML")
    if response.status_code == 200:
        return True

    # Never raise: a broken alert channel must not hide the failure it reports.
    print(f"Telegram send failed: {response.status_code} - {response.text}")

    if plain_fallback is None:
        return False

    print("Retrying without formatting.")
    retry = _post_message(plain_fallback)
    if retry.status_code != 200:
        print(f"Plain retry failed too: {retry.status_code} - {retry.text}")
        return False
    return True


def tail(path, n_lines=LOG_TAIL_LINES):
    """Last n_lines of a log file, or None if it isn't there.

    Only the final LOG_TAIL_MAX_BYTES are read: intraday.log grows without bound
    and a crash puts the useful part (the exception) at the very end anyway.
    """
    if not path.exists():
        return None

    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(0, size - LOG_TAIL_MAX_BYTES))
        chunk = f.read()

    lines = chunk.decode("utf-8", errors="replace").splitlines()
    return "\n".join(lines[-n_lines:])


def collect_logs():
    """(name, last-modified, tail) for each cron log that exists.

    The modification time is part of the diagnosis: a log that stopped being
    written says something different from a log full of tracebacks.
    """
    collected = []
    for path in LOG_FILES:
        text = tail(path)
        if text is None:
            continue
        mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime)
        collected.append((path.name, mtime.strftime("%Y-%m-%d %H:%M"), text))
    return collected


def _escape_html(text):
    """Escape the three characters Telegram's HTML parse mode cares about."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _trim(text, limit):
    """Cut to limit, then drop a half-written HTML entity left at the end.

    `&amp;` sliced into `&am` would make Telegram reject the whole message.
    """
    return re.sub(r"&[a-zA-Z]{0,5}$", "", text[:limit])


def format_alert(problems, today, logs=None, html=False):
    """Build the alert. States what was observed and attaches the logs, nothing more.

    Deliberately offers no theory about the cause: the watchdog sees stale data
    in a bucket, which is consistent with an expired token, a dead network, a
    GCS problem, or a bug. The log tail lets the reader decide.

    With html=True the log tails are wrapped in a language-tagged <pre><code> so
    Telegram renders them as plain monospace blocks. Truncation happens per log
    section rather than on the finished string, so the block always gets closed
    and the problem lines are never the part that gets cut.
    """
    escape = _escape_html if html else (lambda s: s)
    marker = "\n[truncated]"

    lines = [f"⚠️ Wandern Eric watchdog ({today}):", ""]
    lines += [f"• {escape(p)}" for p in problems]
    message = "\n".join(lines)

    if len(message) > TELEGRAM_MAX_CHARS:
        return _trim(message, TELEGRAM_MAX_CHARS - len(marker)) + marker

    opening_tag, closing_tag = (
        (f'<pre><code class="language-{LOG_CODE_LANGUAGE}">', "</code></pre>")
        if html
        else ("", "")
    )

    for name, mtime, text in logs or []:
        header = f"\n\n{escape(f'--- {name} (last written {mtime}) ---')}\n"
        overhead = len(header) + len(opening_tag) + len(closing_tag)
        room = TELEGRAM_MAX_CHARS - len(message) - overhead

        if room <= len(marker):
            break

        body = escape(text)
        if len(body) > room:
            body = _trim(body, room - len(marker)) + marker
            message += header + opening_tag + body + closing_tag
            break

        message += header + opening_tag + body + closing_tag

    return message


def main():
    parser = argparse.ArgumentParser(
        description="Check that the published step data is fresh; alert via Telegram."
    )
    parser.add_argument(
        "--test-alert",
        action="store_true",
        help="Send a test message to verify the Telegram wiring, then exit.",
    )
    args = parser.parse_args()

    if args.test_alert:
        ok = send_telegram("✅ Wandern Eric watchdog: test alert, wiring works.")
        return 0 if ok else 1

    if not GCP_BUCKET_NAME:
        print("GCP_BUCKET_NAME is not set in .env")
        return 1

    today = datetime.date.today()
    problems = run_checks(today)

    if not problems:
        print(f"[watchdog] {today} OK: data.json has yesterday, today.json is fresh.")
        return 0

    logs = collect_logs()
    plain = format_alert(problems, today, logs)
    print(plain)
    send_telegram(format_alert(problems, today, logs, html=True), plain_fallback=plain)
    return 1


if __name__ == "__main__":
    sys.exit(main())
