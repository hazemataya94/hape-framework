from __future__ import annotations

import pytest

from tests.api.test_api_auth_and_parity import MANAGED_OPERATIONS, SOURCE_OPERATIONS, _build_test_client, _product_headers
from tests.github.test_github_app_service import CLOCK, _grant, _service


def test_operator_token_still_reaches_legacy_create_route(monkeypatch, tmp_path) -> None:
    from tests.api.test_api_auth_and_parity import _FakeGitHubService

    monkeypatch.setattr("api.routers.github_router.GitHubService", _FakeGitHubService)
    client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path)
    token_response = client.post("/auth/tokens", headers={"X-Hape-Admin-Key": "admin-key"}, json={"name": "operator"})
    headers = {"Authorization": f"Bearer {token_response.json()['token']}"}
    response = client.post("/github/create/repo", headers=headers, json={"org": "example-org", "name": "service-a"})
    assert response.status_code == 200


def test_setup_url_route_returns_redacted_receipt(monkeypatch, tmp_path) -> None:
    service, _client = _service()
    test_client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path)
    test_client.app.state.github_app_service = service
    headers = _product_headers(test_client, "source-read", SOURCE_OPERATIONS)
    grant = _grant(
        "installation.setup_url",
        {
            "hapeAccountId": "11111111-1111-1111-1111-111111111111",
            "browserSessionId": "sess-aaa",
            "returnPath": "/workspace/33333333-3333-3333-3333-333333333333",
            "sourceImportRegistrationId": "source-import",
            "setupState": "ab" * 32,
        },
        nonce="route-1",
    )
    response = test_client.post("/github/v1/installations/setup-url", headers=headers, json={"idempotencyKey": "route-setup", "grant": grant})
    assert response.status_code == 200
    payload = response.json()
    assert payload["operation"] == "installation.setup_url"
    assert "ghs_" not in str(payload)
    assert "BEGIN" not in str(payload)


def test_managed_token_cannot_call_source_snapshot_route(monkeypatch, tmp_path) -> None:
    test_client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path)
    headers = _product_headers(test_client, "managed-write", MANAGED_OPERATIONS)
    grant = _grant("snapshot.read", {"installationId": 101}, nonce="route-deny")
    response = test_client.post("/github/v1/snapshots/read", headers=headers, json={"idempotencyKey": "deny", "grant": grant})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "policy_denied"


def test_fixture_clock_matches_contract_clock() -> None:
    assert CLOCK.isoformat().replace("+00:00", "Z") == "2026-09-13T10:00:00Z"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
