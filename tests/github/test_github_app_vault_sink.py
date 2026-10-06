from __future__ import annotations

import json

import pytest

from services.github_app_service import GitHubAppError, GitHubAppService
from tests.github.test_github_app_service import CLOCK, FixtureGitHubAppClient, _grant, _source_bindings
from services.github_app_vault_sink import (
    CallableVaultFieldReader,
    VaultKvCredentialSink,
    create_github_app_credential_sink,
    parse_kv_logical_path,
)


SOURCE_PATH = "secret/example-org/framework/hape-framework/dev/github-apps/source-import"
MANAGED_PATH = "secret/example-org/framework/hape-framework/dev/github-apps/managed-repositories"


def _valid_fields() -> dict[str, dict[str, str]]:
    return {
        SOURCE_PATH: {
            "app_id": "1001",
            "client_id": "Iv1.example-source",
            "client_secret": "dummy-source-client-secret",
            "slug": "loaded-source-import",
            "private_key_pem": "dummy-source-pem",
            "expected_permissions": json.dumps({"metadata": "read", "contents": "read"}, separators=(",", ":")),
        },
        MANAGED_PATH: {
            "app_id": "2002",
            "private_key_pem": "dummy-managed-pem",
            "expected_permissions": json.dumps({"contents": "write", "administration": "write"}, separators=(",", ":")),
            "organization_allowlist": "example-org",
        },
    }


def test_vault_sink_loads_required_fields_and_keeps_dummy_org() -> None:
    reader = CallableVaultFieldReader(lambda path: _valid_fields()[path])
    sink = VaultKvCredentialSink(reader, source_import_path=SOURCE_PATH, managed_repositories_path=MANAGED_PATH)
    source = sink.get_registration("source-read")
    managed = sink.get_registration("managed-write")
    assert source.slug == "loaded-source-import"
    assert source.client_id == "Iv1.example-source"
    assert source.registration_id == "source-import"
    assert managed.organization_allowlist == ("example-org",)
    assert managed.registration_id == "managed-repositories"


def test_vault_sink_fails_closed_when_required_field_is_missing() -> None:
    fields = _valid_fields()
    fields[SOURCE_PATH].pop("client_secret")
    sink = VaultKvCredentialSink(
        CallableVaultFieldReader(lambda path: fields[path]),
        source_import_path=SOURCE_PATH,
        managed_repositories_path=MANAGED_PATH,
    )
    with pytest.raises(GitHubAppError) as exc:
        sink.get_registration("source-read")
    assert exc.value.code == "provider_unavailable"
    assert sink.get_registration("managed-write").app_id == "2002"


def test_create_github_app_credential_sink_defaults_to_empty_memory() -> None:
    sink = create_github_app_credential_sink()
    with pytest.raises(GitHubAppError) as exc:
        sink.get_registration("source-read")
    assert exc.value.code == "provider_unavailable"


def test_setup_url_uses_loaded_slug_not_fixture_name() -> None:
    sink = VaultKvCredentialSink(
        CallableVaultFieldReader(lambda path: _valid_fields()[path]),
        source_import_path=SOURCE_PATH,
        managed_repositories_path=MANAGED_PATH,
    )
    service = GitHubAppService(client=FixtureGitHubAppClient(), credential_sink=sink, clock=lambda: CLOCK)
    setup = service.create_setup_url(_grant("installation.setup_url", _source_bindings(), nonce="vault-s"), "key-vault-setup")
    assert setup["setupUrl"] == f"https://github.example.com/apps/loaded-source-import/installations/new?state={_source_bindings()['setupState']}"
    assert "example-source-import" not in setup["setupUrl"]


def test_parse_kv_logical_path() -> None:
    mount, relative = parse_kv_logical_path(SOURCE_PATH)
    assert mount == "secret"
    assert relative == "example-org/framework/hape-framework/dev/github-apps/source-import"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
