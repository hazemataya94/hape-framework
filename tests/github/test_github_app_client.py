from __future__ import annotations

from typing import Any

import pytest
import requests

from clients.github_app_client import GitHubAppClient, GitHubAppClientError, GitHubAppRegistration


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = headers or {}
        self.content = b""

    def json(self) -> dict[str, Any]:
        return self._payload


def test_client_uses_authorization_header_and_never_puts_token_in_url(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def fake_request(self, method: str, url: str, headers: dict[str, str], json: dict[str, Any] | None = None, params: dict[str, Any] | None = None, timeout: int | None = None) -> _FakeResponse:
        captured["method"] = method
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return _FakeResponse(200, {"ok": True})

    monkeypatch.setattr(requests.Session, "request", fake_request)
    client = GitHubAppClient(base_url="https://api.github.example.com")
    payload = client.get_repository("ghs_fixture_token_value", "example-org", "source-repo")
    assert payload == {"ok": True}
    assert captured["url"] == "https://api.github.example.com/repos/example-org/source-repo"
    assert "ghs_fixture_token_value" not in captured["url"]
    assert captured["headers"]["Authorization"] == "Bearer ghs_fixture_token_value"
    assert client.request_log[0]["has_authorization"] is True
    assert "ghs_" not in client.request_log[0]["url"]
    assert "Authorization" in client.request_log[0]["header_names"]


def test_client_maps_rate_limit_after_retries(monkeypatch) -> None:
    def fake_request(self, method: str, url: str, headers: dict[str, str], json: dict[str, Any] | None = None, params: dict[str, Any] | None = None, timeout: int | None = None) -> _FakeResponse:
        return _FakeResponse(429, {}, {"Retry-After": "0"})

    monkeypatch.setattr(requests.Session, "request", fake_request)
    monkeypatch.setattr("clients.github_app_client.time.sleep", lambda _: None)
    client = GitHubAppClient(base_url="https://api.github.example.com")
    with pytest.raises(GitHubAppClientError) as exc:
        client.get_installation("ghs_fixture_token_value", 101)
    assert exc.value.code == "rate_limited"


def test_client_does_not_import_subprocess() -> None:
    import clients.github_app_client as module

    assert not hasattr(module, "subprocess")
    assert "subprocess" not in module.__dict__


def test_exchange_user_code_keeps_secrets_out_of_url(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def fake_request(self, method: str, url: str, headers: dict[str, str] | None = None, json: dict[str, Any] | None = None, params: dict[str, Any] | None = None, data: dict[str, Any] | None = None, timeout: int | None = None) -> _FakeResponse:
        captured["url"] = url
        captured["data"] = data
        return _FakeResponse(200, {"access_token": "ghu_fixture_user", "refresh_token": "ghr_fixture_refresh"})

    monkeypatch.setattr(requests.Session, "request", fake_request)
    client = GitHubAppClient(base_url="https://api.github.example.com", oauth_base_url="https://github.example.com")
    registration = GitHubAppRegistration(
        registration_id="source-import",
        app_id="1001",
        private_key_pem="dummy-pem",
        expected_permissions={"metadata": "read"},
        slug="example-source-import",
        client_id="Iv1.example-source",
        client_secret="dummy-source-client-secret",
    )
    payload = client.exchange_user_code(
        registration,
        "fixture-authorization-code",
        "https://app.example.com/github/authorization/callback",
        "fixture-code-verifier",
    )
    assert payload["access_token"] == "ghu_fixture_user"
    assert captured["url"] == "https://github.example.com/login/oauth/access_token"
    assert "dummy-source-client-secret" not in captured["url"]
    assert "fixture-authorization-code" not in captured["url"]
    assert "fixture-code-verifier" not in captured["url"]
    assert "ghu_" not in client.request_log[0]["url"]


def test_live_hosts_stay_off_by_default(monkeypatch) -> None:
    monkeypatch.delenv("HAPE_GITHUB_APP_LIVE_ENABLED", raising=False)
    from core.config import Config

    assert Config.github_app_live_enabled() is False
    assert Config.get_github_app_api_url() == "https://api.github.example.com"
    assert Config.get_github_app_oauth_url() == "https://github.example.com"
    monkeypatch.setenv("HAPE_GITHUB_APP_LIVE_ENABLED", "true")
    assert Config.get_github_app_api_url() == "https://api.github.com"
    assert Config.get_github_app_oauth_url() == "https://github.com"
    monkeypatch.delenv("HAPE_GITHUB_APP_LIVE_ENABLED", raising=False)


def test_registration_keeps_dummy_allowlist() -> None:
    registration = GitHubAppRegistration(
        registration_id="managed-repositories",
        app_id="2002",
        private_key_pem="dummy-pem",
        expected_permissions={"contents": "write"},
        organization_allowlist=("example-org",),
    )
    assert registration.organization_allowlist == ("example-org",)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
