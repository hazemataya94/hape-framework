from __future__ import annotations

import pytest

from services.github_provider.errors import GitHubV2Error
from tests.github.github_v2_support import SUBJECT_ID, build_service, sample_files, signed_request


def _create(service, private_pem, mode: str = "hape_organization", target: str = "", collaborator: str = "octocat", key: str = "create") -> dict:
    files = sample_files()
    _admitted, digest = service._publication.admit_files(files)
    request = {
        "subject_id": SUBJECT_ID,
        "destination_mode": mode,
        "source_snapshot_digest": digest,
        "idempotency_key": key,
        "files": files,
    }
    if collaborator:
        request["collaborator_login"] = collaborator
    if target:
        request["target_binding_id"] = target
    return service.create_private(signed_request(service, private_pem, "managed_repository.create_private", request))


def _verify_customer(service, private_pem, mode: str, installation_id: int, key: str) -> str:
    setup = service.target_setup_url(signed_request(service, private_pem, "managed_target.setup_url", {"idempotency_key": f"setup-{key}", "code_verifier": f"ver-{key}"}))
    verify = signed_request(
        service,
        private_pem,
        "managed_target.verify",
        {
            "idempotency_key": f"verify-{key}",
            "destination_mode": mode,
            "setup_state": setup["setup_state"],
            "code_verifier": f"ver-{key}",
            "installation_id": installation_id,
        },
    )
    receipt = service.target_verify(verify)
    return str(receipt["safe_provider_ids"]["destination_id"])


def test_hape_create_uses_generated_name_and_collaborator() -> None:
    service, provider, private_pem, _public = build_service()
    receipt = _create(service, private_pem)
    name = receipt["safe_provider_ids"]["repository_name"]
    assert name.startswith("hape-mgr-")
    assert len(name) == 25
    assert "octocat" in provider.repositories[name]["collaborators"]
    assert receipt["envelope_version"] == "github.v2"
    assert "runId" not in receipt


def test_customer_modes_do_not_add_collaborator() -> None:
    service, provider, private_pem, _public = build_service()
    org_target = _verify_customer(service, private_pem, "customer_organization", 201, "org")
    org = _create(service, private_pem, mode="customer_organization", target=org_target, collaborator="", key="create-org")
    assert provider.repositories[org["safe_provider_ids"]["repository_name"]]["collaborators"] == []
    user_target = _verify_customer(service, private_pem, "customer_personal", 301, "user")
    user = _create(service, private_pem, mode="customer_personal", target=user_target, collaborator="", key="create-user")
    assert provider.repositories[user["safe_provider_ids"]["repository_name"]]["collaborators"] == []


def test_baseline_artifact_tag_and_dispose() -> None:
    service, provider, private_pem, _public = build_service()
    created = _create(service, private_pem)
    repository_id = created["safe_provider_ids"]["repository_id"]
    files = sample_files()
    baseline = service.publish_baseline(
        signed_request(service, private_pem, "managed_repository.publish_baseline", {"repository_id": repository_id, "idempotency_key": "base-1", "files": files})
    )
    parent = baseline["safe_provider_ids"]["commit_sha"]
    artifact_files = sample_files("# Reviewed\n")
    _admitted, artifact_digest = service._publication.admit_files(artifact_files)
    artifact = service.publish_artifact(
        signed_request(
            service,
            private_pem,
            "managed_repository.publish_artifact",
            {"repository_id": repository_id, "idempotency_key": "art-1", "artifact_digest": artifact_digest, "expected_parent": parent, "files": artifact_files},
        )
    )
    assert artifact["status"] == "succeeded"
    tag = service.publish_tag(signed_request(service, private_pem, "managed_repository.publish_tag", {"repository_id": repository_id, "idempotency_key": "tag-1"}))
    assert tag["safe_provider_ids"]["tag"].startswith("hape-tag-")
    disposed = service.dispose(signed_request(service, private_pem, "managed_repository.dispose", {"repository_id": repository_id, "idempotency_key": "disp-1"}))
    assert disposed["status"] == "succeeded"
    assert provider.repository_exists(created["safe_provider_ids"]["repository_name"]) is False


def test_wrong_parent_and_product_ids_fail() -> None:
    service, _provider, private_pem, _public = build_service()
    created = _create(service, private_pem)
    repository_id = created["safe_provider_ids"]["repository_id"]
    files = sample_files()
    service.publish_baseline(signed_request(service, private_pem, "managed_repository.publish_baseline", {"repository_id": repository_id, "idempotency_key": "base-2", "files": files}))
    artifact_files = sample_files("# Reviewed\n")
    _admitted, artifact_digest = service._publication.admit_files(artifact_files)
    with pytest.raises(GitHubV2Error) as raised:
        service.publish_artifact(
            signed_request(
                service,
                private_pem,
                "managed_repository.publish_artifact",
                {"repository_id": repository_id, "idempotency_key": "art-bad", "artifact_digest": artifact_digest, "expected_parent": "deadbeef", "files": artifact_files},
            )
        )
    assert raised.value.code == "parent_mismatch"
    with pytest.raises(GitHubV2Error) as denied:
        service.publish_artifact(
            signed_request(
                service,
                private_pem,
                "managed_repository.publish_artifact",
                {"repository_id": repository_id, "idempotency_key": "art-ids", "artifact_digest": artifact_digest, "expected_parent": "deadbeef", "files": artifact_files, "runId": "nope"},
            )
        )
    assert denied.value.code == "policy_denied"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
