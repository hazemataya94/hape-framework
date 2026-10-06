from __future__ import annotations

from tests.api.test_api_auth_and_parity import MANAGED_OPERATIONS, _build_test_client, _product_headers
from tests.github.github_v2_support import SUBJECT_ID, build_service, sample_files, sign_grant, signed_request

V2_OPERATIONS = [
    "managed_destination.status",
    "managed_target.setup_url",
    "managed_target.verify",
    "managed_target.status",
    "managed_repository.create_private",
    "managed_repository.publish_baseline",
    "managed_repository.publish_artifact",
    "managed_repository.publish_tag",
    "managed_repository.dispose",
    "provider_operation.get",
    "provider_receipt.get",
]


def _v2_headers(client) -> dict[str, str]:
    return _product_headers(client, "managed-write", V2_OPERATIONS)


def _attach_service(client):
    service, provider, private_pem, _public = build_service()
    client.app.state.github_v2_service = service
    return service, provider, private_pem


def test_v1_token_cannot_call_v2(monkeypatch, tmp_path) -> None:
    client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path)
    headers = _product_headers(client, "managed-write", MANAGED_OPERATIONS)
    response = client.post("/github/v2/managed-repositories", headers=headers, json={"authorization_grant": "x", "operation_id": "op"})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "policy_denied"


def test_v2_token_cannot_call_v1(monkeypatch, tmp_path) -> None:
    client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path)
    headers = _v2_headers(client)
    response = client.post("/github/v1/repositories", headers=headers, json={"idempotencyKey": "k", "grant": {"grantId": "g"}})
    assert response.status_code == 403


def test_v2_create_and_receipt_round_trip(monkeypatch, tmp_path) -> None:
    client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path)
    service, _provider, private_pem = _attach_service(client)
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
            "idempotency_key": "api-1",
            "collaborator_login": "octocat",
            "files": [{"path": "README.md", "mode": "100644", "hex_bytes": files[0]["bytes"].hex()}],
        },
    )
    headers = _v2_headers(client)
    response = client.post("/github/v2/managed-repositories", headers=headers, json=request)
    assert response.status_code == 200
    payload = response.json()
    assert payload["envelope_version"] == "github.v2"
    assert payload["safe_provider_ids"]["repository_name"].startswith("hape-mgr-")
    receipt_headers = dict(headers)
    receipt_headers["X-Hape-Grant"] = sign_grant(private_pem, "provider_receipt.get", {"receipt_id": payload["receipt_id"]})
    fetched = client.get(f"/github/v2/provider-receipts/{payload['receipt_id']}", headers=receipt_headers)
    assert fetched.status_code == 200
    assert fetched.json()["receipt_id"] == payload["receipt_id"]


def test_v2_rejects_camel_case_alias(monkeypatch, tmp_path) -> None:
    client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path)
    headers = _v2_headers(client)
    response = client.post("/github/v2/managed-repositories", headers=headers, json={"authorization_grant": "x", "operationId": "op"})
    assert response.status_code in {403, 422}


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__]))
