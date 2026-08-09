"""Tests for the data-freshness checks in watchdog.py. Pure functions, no network."""

import datetime
import re

import watchdog


TODAY = datetime.date(2026, 8, 9)
YESTERDAY = "2026-08-08"


def records(*dates):
    return [{"date": d, "count": 1000} for d in dates]


class TestCheckYesterday:
    def test_passes_when_yesterday_is_present(self):
        assert watchdog.check_yesterday(records("2026-08-07", YESTERDAY), TODAY) is None

    def test_passes_when_today_is_already_present(self):
        """A manual re-run that landed today's record is ahead, not behind."""
        assert (
            watchdog.check_yesterday(records(YESTERDAY, "2026-08-09"), TODAY) is None
        )

    def test_fails_when_yesterday_is_missing(self):
        problem = watchdog.check_yesterday(records("2026-08-06", "2026-08-07"), TODAY)
        assert problem is not None
        assert "2026-08-08" in problem
        assert "1 day(s) behind" in problem

    def test_reports_how_many_days_behind(self):
        problem = watchdog.check_yesterday(records("2026-08-01"), TODAY)
        assert "7 day(s) behind" in problem

    def test_fails_on_empty_data(self):
        assert "no records" in watchdog.check_yesterday([], TODAY)

    def test_ignores_records_without_a_date(self):
        problem = watchdog.check_yesterday(
            [{"count": 1}, {"date": YESTERDAY, "count": 2}], TODAY
        )
        assert problem is None


class TestCheckTodayJson:
    def test_passes_when_dated_today(self):
        assert watchdog.check_today_json({"date": "2026-08-09"}, TODAY) is None

    def test_passes_when_dated_yesterday(self):
        """Before the first intraday run of the day, today.json still holds yesterday."""
        assert watchdog.check_today_json({"date": YESTERDAY}, TODAY) is None

    def test_fails_when_older_than_yesterday(self):
        problem = watchdog.check_today_json({"date": "2026-08-05"}, TODAY)
        assert "stale" in problem
        assert "4 days old" in problem

    def test_fails_when_date_missing(self):
        assert "no date field" in watchdog.check_today_json({}, TODAY)
        assert "no date field" in watchdog.check_today_json(None, TODAY)


class TestRunChecks:
    def test_bucket_read_failure_is_reported_not_raised(self, monkeypatch):
        def boom(_blob):
            raise ConnectionError("bucket unreachable")

        monkeypatch.setattr(watchdog, "fetch_json", boom)

        problems = watchdog.run_checks(TODAY)
        assert len(problems) == 2
        assert all("bucket unreachable" in p for p in problems)

    def test_healthy_bucket_returns_no_problems(self, monkeypatch):
        payloads = {
            "data.json": records("2026-08-07", YESTERDAY),
            "today.json": {"date": "2026-08-09", "count": 42, "intraday": True},
        }
        monkeypatch.setattr(watchdog, "fetch_json", lambda blob: payloads[blob])

        assert watchdog.run_checks(TODAY) == []


class TestTail:
    def test_returns_the_last_lines(self, tmp_path):
        log = tmp_path / "cron.log"
        log.write_text("\n".join(f"line {i}" for i in range(50)))

        assert watchdog.tail(log, 3) == "line 47\nline 48\nline 49"

    def test_returns_none_for_a_missing_file(self, tmp_path):
        assert watchdog.tail(tmp_path / "nope.log") is None

    def test_reads_only_the_end_of_a_huge_log(self, tmp_path):
        log = tmp_path / "intraday.log"
        log.write_text("x" * 200_000 + "\nthe actual error")

        assert watchdog.tail(log, 1) == "the actual error"

    def test_survives_undecodable_bytes(self, tmp_path):
        log = tmp_path / "cron.log"
        log.write_bytes(b"fine\n\xff\xfe broken bytes\nlast line")

        assert watchdog.tail(log, 1) == "last line"


class TestCollectLogs:
    def test_skips_logs_that_do_not_exist(self, tmp_path, monkeypatch):
        present = tmp_path / "cron.log"
        present.write_text("boom")
        monkeypatch.setattr(
            watchdog, "LOG_FILES", [present, tmp_path / "intraday.log"]
        )

        collected = watchdog.collect_logs()
        assert len(collected) == 1
        name, mtime, text = collected[0]
        assert name == "cron.log"
        assert text == "boom"
        assert len(mtime) == 16  # YYYY-MM-DD HH:MM


class TestFormatAlert:
    def test_states_the_problem_without_speculating_about_the_cause(self):
        message = watchdog.format_alert(["data.json has no records at all."], TODAY)

        assert "data.json has no records at all." in message
        # The watchdog cannot tell a dead token from a network or GCS fault.
        assert "most likely" not in message.lower()
        assert "token" not in message.lower()

    def test_attaches_the_log_tails(self):
        message = watchdog.format_alert(
            ["data.json has no records at all."],
            TODAY,
            [("cron.log", "2026-08-09 05:00", "RefreshError: invalid_grant")],
        )

        assert "cron.log (last written 2026-08-09 05:00)" in message
        assert "RefreshError: invalid_grant" in message

    def test_truncates_to_the_telegram_limit(self):
        message = watchdog.format_alert(
            ["something broke"], TODAY, [("cron.log", "2026-08-09 05:00", "x" * 9000)]
        )

        assert len(message) <= watchdog.TELEGRAM_MAX_CHARS
        assert message.endswith("[truncated]")
        assert "something broke" in message, "the problem must survive truncation"


OPEN_TAG = f'<pre><code class="language-{watchdog.LOG_CODE_LANGUAGE}">'
CLOSE_TAG = "</code></pre>"


class TestFormatAlertHtml:
    def test_wraps_log_tails_in_a_pre_block(self):
        message = watchdog.format_alert(
            ["data.json has no records at all."],
            TODAY,
            [("cron.log", "2026-08-09 05:00", "RefreshError: invalid_grant")],
            html=True,
        )

        assert f"{OPEN_TAG}RefreshError: invalid_grant{CLOSE_TAG}" in message

    def test_tags_the_language_so_telegram_does_not_syntax_highlight(self):
        """An unlabelled <pre> gets auto-detected, colouring tracebacks as Python."""
        message = watchdog.format_alert(
            ["broke"],
            TODAY,
            [("cron.log", "2026-08-09 05:00", "Traceback (most recent call last):")],
            html=True,
        )

        assert 'class="language-plaintext"' in message
        assert "<pre>Traceback" not in message

    def test_escapes_html_special_characters_in_the_log(self):
        message = watchdog.format_alert(
            ["broke"],
            TODAY,
            [("cron.log", "2026-08-09 05:00", "a < b & c > d <tag>")],
            html=True,
        )

        assert "a &lt; b &amp; c &gt; d &lt;tag&gt;" in message
        assert "<tag>" not in message

    def test_plain_mode_adds_no_markup(self):
        message = watchdog.format_alert(
            ["broke"], TODAY, [("cron.log", "2026-08-09 05:00", "a < b")], html=True
        )
        plain = watchdog.format_alert(
            ["broke"], TODAY, [("cron.log", "2026-08-09 05:00", "a < b")]
        )

        assert OPEN_TAG in message
        assert "<pre" not in plain
        assert "a < b" in plain

    def test_truncation_still_closes_the_pre_tag(self):
        message = watchdog.format_alert(
            ["broke"], TODAY, [("cron.log", "2026-08-09 05:00", "x" * 9000)], html=True
        )

        assert len(message) <= watchdog.TELEGRAM_MAX_CHARS
        assert message.count(OPEN_TAG) == message.count(CLOSE_TAG) == 1
        assert message.endswith(CLOSE_TAG)

    def test_truncation_never_leaves_a_half_written_entity(self):
        """`&amp;` cut into `&am` would make Telegram reject the whole message."""
        # Ampersands land exactly where the cut falls, whatever the limit is.
        message = watchdog.format_alert(
            ["broke"], TODAY, [("cron.log", "2026-08-09 05:00", "&" * 9000)], html=True
        )

        body = message.split(OPEN_TAG)[1].split("[truncated]")[0]
        assert not re.search(r"&[a-zA-Z]{0,5}$", body)

    def test_second_log_is_dropped_rather_than_left_unclosed(self):
        message = watchdog.format_alert(
            ["broke"],
            TODAY,
            [
                ("cron.log", "2026-08-09 05:00", "x" * 9000),
                ("intraday.log", "2026-08-09 09:00", "y" * 9000),
            ],
            html=True,
        )

        assert message.count(OPEN_TAG) == message.count(CLOSE_TAG)
        assert "intraday.log" not in message


class TestSendTelegram:
    def test_sends_with_html_parse_mode(self, monkeypatch):
        monkeypatch.setattr(watchdog, "TELEGRAM_BOT_TOKEN", "token")
        monkeypatch.setattr(watchdog, "TELEGRAM_CHAT_ID", "chat")
        sent = {}

        class Response:
            status_code = 200
            text = "ok"

        def fake_post(_url, json, timeout):
            sent.update(json)
            return Response()

        monkeypatch.setattr(watchdog.requests, "post", fake_post)

        assert watchdog.send_telegram("<pre>log</pre>") is True
        assert sent["parse_mode"] == "HTML"

    def test_falls_back_to_plain_text_when_markup_is_rejected(self, monkeypatch):
        """An alert that arrives ugly beats an alert that never arrives."""
        monkeypatch.setattr(watchdog, "TELEGRAM_BOT_TOKEN", "token")
        monkeypatch.setattr(watchdog, "TELEGRAM_CHAT_ID", "chat")
        attempts = []

        class Response:
            def __init__(self, status_code):
                self.status_code = status_code
                self.text = "can't parse entities"

        def fake_post(_url, json, timeout):
            attempts.append(json)
            return Response(400 if "parse_mode" in json else 200)

        monkeypatch.setattr(watchdog.requests, "post", fake_post)

        assert watchdog.send_telegram("<pre>bad", plain_fallback="plain text") is True
        assert len(attempts) == 2
        assert attempts[1]["text"] == "plain text"
        assert "parse_mode" not in attempts[1]

    def test_reports_failure_when_the_plain_retry_also_fails(self, monkeypatch):
        monkeypatch.setattr(watchdog, "TELEGRAM_BOT_TOKEN", "token")
        monkeypatch.setattr(watchdog, "TELEGRAM_CHAT_ID", "chat")

        class Response:
            status_code = 403
            text = "bot was blocked by the user"

        monkeypatch.setattr(watchdog.requests, "post", lambda *a, **k: Response())

        assert watchdog.send_telegram("<pre>x</pre>", plain_fallback="x") is False


def test_send_telegram_without_config_prints_and_reports_failure(monkeypatch, capsys):
    monkeypatch.setattr(watchdog, "TELEGRAM_BOT_TOKEN", None)
    monkeypatch.setattr(watchdog, "TELEGRAM_CHAT_ID", None)

    assert watchdog.send_telegram("hello") is False
    assert "hello" in capsys.readouterr().out


def test_send_telegram_failure_does_not_raise(monkeypatch):
    """A broken alert channel must not mask the failure it was reporting."""
    monkeypatch.setattr(watchdog, "TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setattr(watchdog, "TELEGRAM_CHAT_ID", "chat")

    class Response:
        status_code = 401
        text = "Unauthorized"

    monkeypatch.setattr(watchdog.requests, "post", lambda *a, **k: Response())
    assert watchdog.send_telegram("hello") is False
