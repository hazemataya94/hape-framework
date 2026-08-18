from __future__ import annotations

from pathlib import Path

import pytest

from core.errors.exceptions import HapeValidationError
from services.vault_service import VaultService


class _FakeVaultClient:
    def __init__(self) -> None:
        self.login_calls: list[tuple[str, str, str, str]] = []
        self.kv_calls: list[tuple[str, str, str, str, str]] = []

    def login_approle(self, vault_addr: str, auth_path: str, role_id: str, secret_id: str) -> str:
        self.login_calls.append((vault_addr, auth_path, role_id, secret_id))
        return "s.test-client-token"

    def kv_v2_read_field(self, vault_addr: str, client_token: str, kv_mount: str, kv_relative_path: str, field: str) -> str:
        self.kv_calls.append((vault_addr, client_token, kv_mount, kv_relative_path, field))
        return "pypi-test-token"


def _write_secret_id(path: Path) -> Path:
    secret_file = path / "secret.id"
    secret_file.write_text("test-approle-secret-id\n", encoding="utf-8")
    return secret_file


def test_kv_get_omit_value_does_not_include_secret(tmp_path: Path) -> None:
    secret_file = _write_secret_id(tmp_path)
    fake_client = _FakeVaultClient()
    vault_service = VaultService(vault_client=fake_client)
    result = vault_service.kv_get(
        omit_value=True,
        vault_addr="https://vault.example.com",
        role_id="test-role-id",
        secret_id_file=str(secret_file),
        auth_path="approle",
        kv_mount="kv",
        kv_relative_path="example/pypi",
        kv_field="token",
    )
    assert result["retrieved"] is True
    assert "value" not in result
    assert "pypi-test-token" not in str(result)
    assert fake_client.login_calls[0][3] == "test-approle-secret-id"
    assert fake_client.kv_calls[0][4] == "token"


def test_kv_get_returns_field_value(tmp_path: Path) -> None:
    secret_file = _write_secret_id(tmp_path)
    vault_service = VaultService(vault_client=_FakeVaultClient())
    result = vault_service.kv_get(
        omit_value=False,
        vault_addr="https://vault.example.com",
        role_id="test-role-id",
        secret_id_file=str(secret_file),
        auth_path="approle",
        kv_mount="kv",
        kv_relative_path="example/pypi",
        kv_field="token",
    )
    assert result["retrieved"] is True
    assert result["value"] == "pypi-test-token"
    assert result["kv_path"] == "example/pypi"


def test_kv_get_requires_secret_id_file(tmp_path: Path) -> None:
    vault_service = VaultService(vault_client=_FakeVaultClient())
    with pytest.raises(HapeValidationError) as exc:
        vault_service.kv_get(
            vault_addr="https://vault.example.com",
            role_id="test-role-id",
            secret_id_file=str(tmp_path / "missing.id"),
        )
    assert exc.value.code == "VAULT_SECRET_ID_FILE_NOT_FOUND"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
