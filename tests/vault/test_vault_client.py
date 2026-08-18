from __future__ import annotations

import pytest

from clients.vault_client import VaultClient


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _FakeSession:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[dict] = []

    def request(self, method: str, url: str, headers: dict | None = None, json: dict | None = None, timeout: int | None = None):
        self.calls.append({"method": method, "url": url, "headers": headers, "json": json, "timeout": timeout})
        return _FakeResponse(self.payload)


def test_login_approle_returns_client_token() -> None:
    session = _FakeSession({"auth": {"client_token": "s.test-client-token"}})
    vault_client = VaultClient(session=session, timeout_seconds=5)  # type: ignore[arg-type]
    token = vault_client.login_approle("https://vault.example.com", "approle", "role-id", "secret-id")
    assert token == "s.test-client-token"
    assert session.calls[0]["url"] == "https://vault.example.com/v1/auth/approle/login"
    assert "secret-id" not in str(session.calls[0]["url"])


def test_kv_v2_read_field_returns_token_field() -> None:
    session = _FakeSession({"data": {"data": {"token": "pypi-test-token"}}})
    vault_client = VaultClient(session=session, timeout_seconds=5)  # type: ignore[arg-type]
    value = vault_client.kv_v2_read_field(
        "https://vault.example.com",
        "s.test-client-token",
        "kv",
        "example/pypi",
        "token",
    )
    assert value == "pypi-test-token"
    assert session.calls[0]["url"] == "https://vault.example.com/v1/kv/data/example/pypi"


def test_kv_v2_read_field_rejects_missing_field() -> None:
    session = _FakeSession({"data": {"data": {}}})
    vault_client = VaultClient(session=session, timeout_seconds=5)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        vault_client.kv_v2_read_field("https://vault.example.com", "s.test", "kv", "example/pypi", "token")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
