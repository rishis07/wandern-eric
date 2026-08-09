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
import sys
import requests

load_dotenv(Path(__file__).parent / ".env")

GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")
PUBLIC_BUCKET_BASE_URL = "https://storage.googleapis.com"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HTTP_TIMEOUT_SECONDS = 20

# today.json is refreshed hourly between 08:00 and 23:00. Anything older than
# yesterday means the intraday job has been down for at least a full day.
TODAY_JSON_MAX_AGE_DAYS = 1


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


def send_telegram(text):
    """Post a message via the Telegram bot API. Returns True when it went out."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(
            "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set in .env, "
            "alert not sent, printing instead:"
        )
        print(text)
        return False

    response = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    if response.status_code != 200:
        # Never raise: a broken alert channel must not hide the failure it reports.
        print(f"Telegram send failed: {response.status_code} - {response.text}")
        return False
    return True


def format_alert(problems, today):
    lines = [f"⚠️ Wandern Eric watchdog ({today}):", ""]
    lines += [f"• {p}" for p in problems]
    lines += [
        "",
        "Most likely the Google Health token expired or was revoked.",
        "Check cron.log / intraday.log on the Pi for RefreshError.",
    ]
    return "\n".join(lines)


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

    message = format_alert(problems, today)
    print(message)
    send_telegram(message)
    return 1


if __name__ == "__main__":
    sys.exit(main())
