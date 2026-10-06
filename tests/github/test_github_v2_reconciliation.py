from __future__ import annotations

import pytest

from services.github_provider.errors import GitHubV2Error
from tests.github.github_v2_support import SUBJECT_ID, build_service, sample_files, signed_request


def test_unknown_create_reconciles_when_provider_has_name() -> None:
    service, provider, private_pem, _public = build_service()
    files = sample_files()
    _admitted, digest = service._publication.admit_files(files)
    provider.next_fail = provider.UNKNOWN
    request = signed_request(
        service,
        private_pem,
        "managed_repository.create_private",
        {
            "subject_id": SUBJECT_ID,
            "destination_mode": "hape_organization",
            "source_snapshot_digest": digest,
            "idempotency_key": "unknown-1",
            "collaborator_login": "octocat",
            "files": files,
        },
    )
    unknown = service.create_private(request)
    assert unknown["status"] == "unknown"
    assert unknown["retry_class"] == "reconcile_then_retry"
    operation = service._repository.get_operation(unknown["operation_id"])
    assert operation is not None
    provider.create_repository("example-org", operation.provider_marker, 11)
    reconciled = service.reconcile(signed_request(service, private_pem, "provider_operation.get", {"operation_id": unknown["operation_id"]}))
    assert reconciled["status"] == "reconciled"
    assert reconciled["retry_class"] == "idempotent_replay"


def test_same_key_different_hash_conflicts() -> None:
    service, _provider, private_pem, _public = build_service()
    files = sample_files()
    _admitted, digest = service._publication.admit_files(files)
    first = signed_request(
        service,
        private_pem,
        "managed_repository.create_private",
        {
            "subject_id": SUBJECT_ID,
            "destination_mode": "hape_organization",
            "source_snapshot_digest": digest,
            "idempotency_key": "conflict-1",
            "collaborator_login": "octocat",
            "files": files,
        },
    )
    service.create_private(first)
    other_files = sample_files("# Other\n")
    _admitted2, digest2 = service._publication.admit_files(other_files)
    second = signed_request(
        service,
        private_pem,
        "managed_repository.create_private",
        {
            "subject_id": SUBJECT_ID,
            "destination_mode": "hape_organization",
            "source_snapshot_digest": digest2,
            "idempotency_key": "conflict-1",
            "collaborator_login": "octocat",
            "files": other_files,
        },
    )
    with pytest.raises(GitHubV2Error) as raised:
        service.create_private(second)
    assert raised.value.code == "conflict"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
