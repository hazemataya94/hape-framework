from __future__ import annotations

import pytest

from services.github_provider.errors import GitHubV2Error
from tests.github.github_v2_support import build_service, sample_files, signed_request


def _create_request(service, extra: dict | None = None) -> dict:
    files = sample_files()
    _admitted, digest = service._publication.admit_files(files)
    request = {
        "subject_id": "sub-create",
        "destination_mode": "hape_organization",
        "source_snapshot_digest": digest,
        "idempotency_key": "create-1",
        "collaborator_login": "octocat",
        "files": files,
    }
    if extra:
        request.update(extra)
    return request


def test_unsigned_grant_is_rejected() -> None:
    service, _provider, _private, _public = build_service()
    with pytest.raises(GitHubV2Error) as raised:
        service.destination_status({"destination_id": "missing", "authorization_grant": ""})
    assert raised.value.code == "unauthorized"


def test_product_identifier_in_grant_is_rejected() -> None:
    service, _provider, private_pem, _public = build_service()
    request = signed_request(service, private_pem, "managed_repository.create_private", _create_request(service), extra={"runId": "run-1"})
    with pytest.raises(GitHubV2Error) as raised:
        service.create_private(request)
    assert raised.value.code == "policy_denied"


def test_nested_product_identifier_in_constraints_is_rejected() -> None:
    service, _provider, private_pem, _public = build_service()
    extra = {"resource_constraints": {"destination_mode": "hape_organization", "collaborator_login": "octocat", "run_id": "hidden"}}
    request = signed_request(service, private_pem, "managed_repository.create_private", _create_request(service), extra=extra)
    with pytest.raises(GitHubV2Error) as raised:
        service.create_private(request)
    assert raised.value.code == "policy_denied"


def test_unknown_constraint_key_is_rejected() -> None:
    service, _provider, private_pem, _public = build_service()
    extra = {"resource_constraints": {"destination_mode": "hape_organization", "collaborator_login": "octocat", "owner": "evil"}}
    request = signed_request(service, private_pem, "managed_repository.create_private", _create_request(service), extra=extra)
    with pytest.raises(GitHubV2Error) as raised:
        service.create_private(request)
    assert raised.value.code == "invalid_resource_constraints"


def test_grant_replay_is_rejected() -> None:
    service, _provider, private_pem, _public = build_service()
    destination = service._destinations.ensure_hape_destination()
    request = signed_request(service, private_pem, "managed_destination.status", {"destination_id": destination.destination_id})
    first = service.destination_status(request)
    assert first["mode"] == "hape_organization"
    with pytest.raises(GitHubV2Error) as raised:
        service.destination_status(request)
    assert raised.value.code == "grant_replayed"


def test_same_key_same_hash_replays_receipt() -> None:
    service, _provider, private_pem, _public = build_service()
    request = signed_request(service, private_pem, "managed_repository.create_private", _create_request(service))
    first = service.create_private(request)
    second = service.create_private(request)
    assert first["receipt_id"] == second["receipt_id"]
    assert first["envelope_version"] == "github.v2"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
