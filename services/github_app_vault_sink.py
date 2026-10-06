from __future__ import annotations

import json
from typing import Callable, Protocol

from clients.github_app_client import GitHubAppRegistration
from clients.vault_client import VaultClient
from core.config import Config
from core.logging import LocalLogging
from services.github_app_service import GitHubAppError, VaultAgentMemoryCredentialSink


class VaultFieldMapReader(Protocol):
    def read_fields(self, logical_path: str) -> dict[str, str]: ...


class GitHubAppCredentialSinkError(Exception):
    pass


SOURCE_READ_REQUIRED_FIELDS = (
    "app_id",
    "client_id",
    "client_secret",
    "slug",
    "private_key_pem",
    "expected_permissions",
)
MANAGED_WRITE_REQUIRED_FIELDS = (
    "app_id",
    "private_key_pem",
    "expected_permissions",
    "organization_allowlist",
)
ROLE_REGISTRATION_IDS = {
    "source-read": "source-import",
    "managed-write": "managed-repositories",
}


def parse_kv_logical_path(logical_path: str) -> tuple[str, str]:
    parts = [part for part in logical_path.strip().strip("/").split("/") if part]
    if len(parts) < 2:
        raise GitHubAppCredentialSinkError("invalid_vault_path")
    return parts[0], "/".join(parts[1:])


def parse_expected_permissions(raw_value: str) -> dict[str, str]:
    payload = json.loads(raw_value)
    if not isinstance(payload, dict) or not payload:
        raise GitHubAppCredentialSinkError("invalid_permissions")
    parsed = {str(key): str(value) for key, value in payload.items()}
    if any(not key or not value for key, value in parsed.items()):
        raise GitHubAppCredentialSinkError("invalid_permissions")
    return parsed


def parse_organization_allowlist(raw_value: str) -> tuple[str, ...]:
    items = tuple(item.strip() for item in raw_value.split(",") if item.strip())
    if not items:
        raise GitHubAppCredentialSinkError("invalid_allowlist")
    return items


class VaultKvCredentialSink:
    def __init__(
        self,
        reader: VaultFieldMapReader,
        *,
        source_import_path: str | None = None,
        managed_repositories_path: str | None = None,
    ) -> None:
        self.logger = LocalLogging.get_logger("hape.git_hub_app_vault_sink")
        self._reader = reader
        self._source_import_path = source_import_path or Config.get_github_app_source_import_vault_path()
        self._managed_repositories_path = managed_repositories_path or Config.get_github_app_managed_repositories_vault_path()
        self._memory: dict[str, GitHubAppRegistration] = {}
        self._load()

    def _load(self) -> None:
        self._try_load_role(
            "source-read",
            self._source_import_path,
            SOURCE_READ_REQUIRED_FIELDS,
            require_allowlist=False,
        )
        self._try_load_role(
            "managed-write",
            self._managed_repositories_path,
            MANAGED_WRITE_REQUIRED_FIELDS,
            require_allowlist=True,
        )

    def _try_load_role(self, role: str, logical_path: str, required_fields: tuple[str, ...], *, require_allowlist: bool) -> None:
        try:
            fields = self._reader.read_fields(logical_path)
            missing = [field_name for field_name in required_fields if not str(fields.get(field_name) or "").strip()]
            if missing:
                raise GitHubAppCredentialSinkError("missing_fields")
            expected_permissions = parse_expected_permissions(fields["expected_permissions"])
            organization_allowlist = parse_organization_allowlist(fields.get("organization_allowlist", "")) if require_allowlist else ()
            self._memory[role] = GitHubAppRegistration(
                registration_id=ROLE_REGISTRATION_IDS[role],
                app_id=fields["app_id"],
                private_key_pem=fields["private_key_pem"],
                expected_permissions=expected_permissions,
                organization_allowlist=organization_allowlist,
                slug=fields.get("slug", ""),
                client_id=fields.get("client_id", ""),
                client_secret=fields.get("client_secret", ""),
            )
            self.logger.info("github_app_registration_loaded role=%s", role)
        except Exception:
            self.logger.info("github_app_registration_unavailable role=%s", role)

    def get_registration(self, role: str) -> GitHubAppRegistration:
        registration = self._memory.get(role)
        if registration is None:
            raise GitHubAppError("provider_unavailable")
        return registration


class ConfigVaultTokenReader:
    def __init__(self, vault_client: VaultClient | None = None) -> None:
        self._client = vault_client or VaultClient()

    def read_fields(self, logical_path: str) -> dict[str, str]:
        token = Config.get_vault_token()
        if not token:
            raise GitHubAppCredentialSinkError("vault_token_missing")
        mount, relative = parse_kv_logical_path(logical_path)
        return self._client.kv_v2_read_fields(Config.get_vault_addr(), token, mount, relative)


def create_github_app_credential_sink(reader: VaultFieldMapReader | None = None) -> VaultAgentMemoryCredentialSink | VaultKvCredentialSink:
    if reader is None and Config.github_app_vault_sink_enabled():
        reader = ConfigVaultTokenReader()
    if reader is None:
        return VaultAgentMemoryCredentialSink()
    return VaultKvCredentialSink(reader)


class CallableVaultFieldReader:
    def __init__(self, callback: Callable[[str], dict[str, str]]) -> None:
        self._callback = callback

    def read_fields(self, logical_path: str) -> dict[str, str]:
        return self._callback(logical_path)
