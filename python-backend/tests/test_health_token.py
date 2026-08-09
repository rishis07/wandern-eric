"""Tests for the Google Health token persistence / refresh logic in main.py.

No network, no Google Health API calls. Everything here is local file I/O and
stubs (running the real API off the Pi is forbidden, see CLAUDE.md).
"""

from google.auth.exceptions import RefreshError
import datetime
import json
import pytest

import main


def utcnow():
    """Naive UTC now, the form google-auth stores in `Credentials.expiry`."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


@pytest.fixture
def token_path(tmp_path, monkeypatch):
    path = tmp_path / "secrets" / "token_health.json"
    monkeypatch.setattr(main, "HEALTH_TOKEN_PATH", path)
    return path


class FakeCreds:
    """Just the attributes save_health_token reads off a Credentials object."""

    def __init__(self, token="access-1", refresh_token="refresh-1", expiry=None):
        self.token = token
        self.refresh_token = refresh_token
        self.token_uri = "https://oauth2.googleapis.com/token"
        self.client_id = "client-id"
        self.client_secret = "client-secret"
        self.scopes = main.HEALTH_SCOPES
        self.expiry = expiry


def test_save_token_persists_expiry_and_scopes(token_path):
    expiry = datetime.datetime(2026, 8, 9, 12, 30, 0)
    main.save_health_token(FakeCreds(expiry=expiry))

    stored = json.loads(token_path.read_text())
    assert stored["expiry"] == expiry.isoformat()
    assert stored["scopes"] == main.HEALTH_SCOPES
    assert stored["refresh_token"] == "refresh-1"


def test_save_load_round_trip_preserves_expiry(token_path):
    expiry = datetime.datetime(2026, 8, 9, 12, 30, 0)
    main.save_health_token(FakeCreds(expiry=expiry))

    creds = main.load_health_credentials()
    assert creds.expiry == expiry
    assert creds.token == "access-1"
    assert creds.refresh_token == "refresh-1"
    assert creds.scopes == main.HEALTH_SCOPES


def test_load_returns_none_when_no_token_file(token_path):
    assert main.load_health_credentials() is None


def test_legacy_token_without_expiry_is_treated_as_stale(token_path):
    """Regression: token files written before expiry was persisted.

    google-auth reports `expiry=None` credentials as valid forever, which made
    the whole refresh branch unreachable and left the refreshed token unsaved.
    """
    token_path.parent.mkdir(parents=True)
    token_path.write_text(
        json.dumps(
            {
                "token": "stale-access-token",
                "refresh_token": "refresh-1",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": "client-id",
                "client_secret": "client-secret",
            }
        )
    )

    creds = main.load_health_credentials()
    assert creds.expiry is None
    assert creds.valid is True, "google-auth still calls an expiry-less token valid"
    assert main.needs_refresh(creds) is True


def test_unexpired_token_does_not_need_refresh(token_path):
    future = utcnow() + datetime.timedelta(hours=1)
    main.save_health_token(FakeCreds(expiry=future))

    assert main.needs_refresh(main.load_health_credentials()) is False


def test_expired_token_needs_refresh(token_path):
    past = utcnow() - datetime.timedelta(hours=1)
    main.save_health_token(FakeCreds(expiry=past))

    assert main.needs_refresh(main.load_health_credentials()) is True


def test_timezone_aware_expiry_is_normalised_to_naive_utc(token_path):
    aware = datetime.datetime(
        2026, 8, 9, 14, 30, tzinfo=datetime.timezone(datetime.timedelta(hours=2))
    )
    token_path.parent.mkdir(parents=True)
    token_path.write_text(
        json.dumps({"token": "t", "refresh_token": "r", "expiry": aware.isoformat()})
    )

    creds = main.load_health_credentials()
    assert creds.expiry == datetime.datetime(2026, 8, 9, 12, 30)
    assert creds.expiry.tzinfo is None


class TestControllerSession:
    """__get_session must fail loudly instead of opening a browser on the Pi."""

    def test_missing_token_file_raises_instead_of_browser_flow(
        self, token_path, monkeypatch
    ):
        def explode(*_args, **_kwargs):
            raise AssertionError("browser OAuth flow must never run implicitly")

        monkeypatch.setattr(main, "run_health_oauth_flow", explode)

        with pytest.raises(main.HealthAuthError, match="No token at"):
            main.GoogleHealthController()

    def test_token_without_refresh_token_raises(self, token_path):
        main.save_health_token(FakeCreds(refresh_token=None))

        with pytest.raises(main.HealthAuthError, match="no refresh_token"):
            main.GoogleHealthController()

    def test_refresh_error_becomes_health_auth_error(self, token_path, monkeypatch):
        class DeadCreds(FakeCreds):
            def refresh(self, _request):
                raise RefreshError(
                    "invalid_grant: Token has been expired or revoked.",
                    {"error": "invalid_grant"},
                )

        monkeypatch.setattr(main, "load_health_credentials", lambda: DeadCreds())

        with pytest.raises(main.HealthAuthError) as excinfo:
            main.GoogleHealthController()

        assert "invalid_grant" in str(excinfo.value)
        assert "--auth" in str(excinfo.value), "must tell the operator how to recover"

    def test_stale_token_is_refreshed_and_saved(self, token_path, monkeypatch):
        saved = []

        class RefreshableCreds(FakeCreds):
            def refresh(self, _request):
                self.token = "access-2"
                self.expiry = utcnow() + datetime.timedelta(hours=1)

        monkeypatch.setattr(main, "load_health_credentials", lambda: RefreshableCreds())
        monkeypatch.setattr(main, "save_health_token", lambda creds: saved.append(creds))
        monkeypatch.setattr(main, "Request", lambda: None)
        monkeypatch.setattr(
            main, "PersistingAuthorizedSession", lambda creds: ("session", creds)
        )

        controller = main.GoogleHealthController()

        assert saved, "refreshed credentials must be written back to disk"
        assert saved[0].token == "access-2"
        assert controller.session[1].token == "access-2"


def test_persisting_session_saves_after_inflight_refresh(monkeypatch):
    """A 401-triggered refresh inside AuthorizedSession must reach the disk."""
    creds = FakeCreds()
    saved = []
    monkeypatch.setattr(main, "save_health_token", lambda c: saved.append(c.token))

    def fake_request(self, *_args, **_kwargs):
        self.credentials.token = "access-refreshed"
        return "response"

    monkeypatch.setattr(main.AuthorizedSession, "request", fake_request)

    session = main.PersistingAuthorizedSession(creds)
    assert session.request("GET", "https://example.test") == "response"
    assert saved == ["access-refreshed"]


def test_persisting_session_does_not_save_when_token_unchanged(monkeypatch):
    creds = FakeCreds()
    saved = []
    monkeypatch.setattr(main, "save_health_token", lambda c: saved.append(c.token))
    monkeypatch.setattr(
        main.AuthorizedSession, "request", lambda self, *a, **k: "response"
    )

    main.PersistingAuthorizedSession(creds).request("GET", "https://example.test")
    assert saved == []
