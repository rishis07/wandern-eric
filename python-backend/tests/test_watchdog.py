"""Tests for the data-freshness checks in watchdog.py. Pure functions, no network."""

import datetime

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


def test_alert_message_mentions_the_likely_cause():
    message = watchdog.format_alert(["data.json has no records at all."], TODAY)
    assert "token" in message.lower()
    assert "data.json has no records at all." in message


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
