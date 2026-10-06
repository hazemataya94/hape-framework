from __future__ import annotations

from tests.github.github_v2_support import SUBJECT_ID, build_service, sample_files, signed_request


def test_restart_preserves_grant_target_repository_and_receipt(tmp_path) -> None:
    sqlite_path = str(tmp_path / "github-provider.sqlite")
    service, _provider, private_pem, public_pem = build_service(sqlite_path=sqlite_path)
    files = sample_files()
    _admitted, digest = service._publication.admit_files(files)
    request = signed_request(
        service,
        private_pem,
        "managed_repository.create_private",
        {
            "subject_id": SUBJECT_ID,
            "destination_mode": "hape_organization",
            "source_snapshot_digest": digest,
            "idempotency_key": "persist-1",
            "collaborator_login": "octocat",
            "files": files,
        },
    )
    created = service.create_private(request)
    receipt_id = created["receipt_id"]
    repository_id = created["safe_provider_ids"]["repository_id"]
    restarted, _provider2, _private, _public = build_service(sqlite_path=sqlite_path, private_pem=private_pem, public_pem=public_pem)
    stored = restarted._repository.get_repository(repository_id)
    assert stored is not None
    assert stored.repository_name.startswith("hape-mgr-")
    assert restarted._repository.grant_consumed(restarted._repository.get_operation(created["operation_id"]).grant_jti)
    replayed = restarted.create_private(request)
    assert replayed["receipt_id"] == receipt_id
    fetched = restarted.get_receipt(signed_request(restarted, private_pem, "provider_receipt.get", {"receipt_id": receipt_id}))
    assert fetched["envelope_version"] == "github.v2"
    assert fetched["subject_id"] == SUBJECT_ID


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__]))
