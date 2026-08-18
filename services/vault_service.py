from __future__ import annotations

from pathlib import Path
from typing import Any

from requests import HTTPError

from clients.vault_client import VaultClient
from core.config import Config
from core.errors.exceptions import HapeExternalError, HapeValidationError
from core.errors.messages.vault_error_messages import get_vault_error_message
from core.logging import LocalLogging


class VaultService:
    DEFAULT_SECRET_ID_FILENAME = "secret.id"
    DEFAULT_AUTH_PATH = "approle"
    DEFAULT_KV_MOUNT = "kv"
    DEFAULT_KV_RELATIVE_PATH = "example/pypi"
    DEFAULT_KV_FIELD = "token"

    def __init__(self, vault_client: VaultClient | None = None) -> None:
        self.vault_client = vault_client or VaultClient()
        self.logger = LocalLogging.get_logger("hape.vault_service")

    def _read_secret_id(self, secret_id_file: Path) -> str:
        if not secret_id_file.exists():
            raise HapeValidationError(
                code="VAULT_SECRET_ID_FILE_NOT_FOUND",
                message=get_vault_error_message("VAULT_SECRET_ID_FILE_NOT_FOUND", secret_id_file=str(secret_id_file)),
            )
        secret_id = secret_id_file.read_text(encoding="utf-8").strip()
        if not secret_id:
            raise HapeValidationError(
                code="VAULT_SECRET_ID_FILE_EMPTY",
                message=get_vault_error_message("VAULT_SECRET_ID_FILE_EMPTY", secret_id_file=str(secret_id_file)),
            )
        return secret_id

    def _resolve_secret_id_file(self, secret_id_file: str | None) -> Path:
        if secret_id_file:
            return Path(secret_id_file).expanduser()
        configured = Config.get_vault_secret_id_file()
        if configured:
            return Path(configured).expanduser()
        workspace_root = Config.get_workspace_root()
        if workspace_root:
            return Path(workspace_root).expanduser() / self.DEFAULT_SECRET_ID_FILENAME
        raise HapeValidationError(code="VAULT_SECRET_ID_FILE_REQUIRED", message=get_vault_error_message("VAULT_SECRET_ID_FILE_REQUIRED"))

    def _read_kv_field(
        self,
        *,
        vault_addr: str | None,
        role_id: str | None,
        secret_id_file: str | None,
        auth_path: str | None,
        kv_mount: str | None,
        kv_relative_path: str | None,
        kv_field: str | None,
    ) -> tuple[str, str, str, str]:
        resolved_addr = (vault_addr or Config.get_vault_addr()).rstrip("/")
        resolved_role_id = (role_id or Config.get_vault_role_id()).strip()
        if not resolved_role_id:
            raise HapeValidationError(code="VAULT_ROLE_ID_REQUIRED", message=get_vault_error_message("VAULT_ROLE_ID_REQUIRED"))
        resolved_auth_path = (auth_path or Config.get_vault_auth_path()).strip("/")
        resolved_mount = (kv_mount or Config.get_vault_kv_mount()).strip("/")
        resolved_path = (kv_relative_path or Config.get_vault_kv_relative_path()).strip("/")
        resolved_field = (kv_field or Config.get_vault_kv_field()).strip()
        secret_id = self._read_secret_id(self._resolve_secret_id_file(secret_id_file))
        try:
            client_token = self.vault_client.login_approle(resolved_addr, resolved_auth_path, resolved_role_id, secret_id)
        except (HTTPError, ValueError) as exc:
            raise HapeExternalError(code="VAULT_LOGIN_FAILED", message=get_vault_error_message("VAULT_LOGIN_FAILED")) from exc
        kv_logical_path = f"{resolved_mount}/data/{resolved_path}"
        try:
            value = self.vault_client.kv_v2_read_field(resolved_addr, client_token, resolved_mount, resolved_path, resolved_field)
        except (HTTPError, ValueError) as exc:
            raise HapeExternalError(code="VAULT_KV_READ_FAILED", message=get_vault_error_message("VAULT_KV_READ_FAILED", kv_path=kv_logical_path)) from exc
        return resolved_mount, resolved_path, resolved_field, value

    def kv_get(
        self,
        *,
        omit_value: bool = False,
        vault_addr: str | None = None,
        role_id: str | None = None,
        secret_id_file: str | None = None,
        auth_path: str | None = None,
        kv_mount: str | None = None,
        kv_relative_path: str | None = None,
        kv_field: str | None = None,
    ) -> dict[str, Any]:
        resolved_mount, resolved_path, resolved_field, value = self._read_kv_field(
            vault_addr=vault_addr,
            role_id=role_id,
            secret_id_file=secret_id_file,
            auth_path=auth_path,
            kv_mount=kv_mount,
            kv_relative_path=kv_relative_path,
            kv_field=kv_field,
        )
        self.logger.info("kv_get mount=%s path=%s field=%s omit_value=%s", resolved_mount, resolved_path, resolved_field, omit_value)
        result: dict[str, Any] = {
            "retrieved": True,
            "kv_mount": resolved_mount,
            "kv_path": resolved_path,
            "kv_field": resolved_field,
        }
        if omit_value:
            return result
        result["value"] = value
        return result


if __name__ == "__main__":
    print(VaultService.DEFAULT_SECRET_ID_FILENAME)
    print(VaultService.DEFAULT_KV_RELATIVE_PATH)
