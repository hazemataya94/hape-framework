"""Vault HTTP client for AppRole login and KV v2 reads."""

from __future__ import annotations

from typing import Any

import requests

from core.logging import LocalLogging


class VaultClient:
    DEFAULT_TIMEOUT_SECONDS = 30
    DEFAULT_ADDR = "https://vault.example.com"

    def __init__(self, session: requests.Session | None = None, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> None:
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds
        self.logger = LocalLogging.get_logger("hape.vault_client")

    def _request_json(self, method: str, url: str, *, headers: dict[str, str] | None = None, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
        self.logger.debug("vault_http method=%s", method)
        response = self.session.request(method=method, url=url, headers=headers, json=json_body, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Vault response must be a JSON object.")
        return payload

    def login_approle(self, vault_addr: str, auth_path: str, role_id: str, secret_id: str) -> str:
        login_url = f"{vault_addr.rstrip('/')}/v1/auth/{auth_path.strip('/')}/login"
        payload = self._request_json("POST", login_url, json_body={"role_id": role_id, "secret_id": secret_id})
        auth = payload.get("auth")
        if not isinstance(auth, dict):
            raise ValueError("Vault AppRole login response is missing auth.")
        client_token = str(auth.get("client_token", "")).strip()
        if not client_token:
            raise ValueError("Vault AppRole login response is missing client_token.")
        self.logger.info("approle_login auth_path=%s", auth_path)
        return client_token

    def kv_v2_read_field(self, vault_addr: str, client_token: str, kv_mount: str, kv_relative_path: str, field: str) -> str:
        read_url = f"{vault_addr.rstrip('/')}/v1/{kv_mount.strip('/')}/data/{kv_relative_path.strip('/')}"
        payload = self._request_json("GET", read_url, headers={"X-Vault-Token": client_token})
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ValueError("Vault KV response is missing data.")
        inner = data.get("data")
        if not isinstance(inner, dict):
            raise ValueError("Vault KV response is missing data.data.")
        value = inner.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Vault KV field '{field}' is missing or empty.")
        self.logger.info("kv_v2_read mount=%s path=%s field=%s", kv_mount, kv_relative_path, field)
        return value.strip()


if __name__ == "__main__":
    print(VaultClient.DEFAULT_ADDR)
    print(VaultClient.DEFAULT_TIMEOUT_SECONDS)
