from __future__ import annotations

from fastapi.testclient import TestClient


class _FakeGitHubService:
    last_create_call: dict[str, object] = {}
    last_list_call: dict[str, object] = {}
    user_info_calls: int = 0
    last_delete_call: dict[str, object] = {}

    def create_repository(
        self,
        org: str,
        name: str,
        visibility: str = "private",
        write_collaborator_email: str = "",
        write_collaborator_login: str = "",
    ) -> dict[str, object]:
        _FakeGitHubService.last_create_call = {
            "org": org,
            "name": name,
            "visibility": visibility,
        }
        return {
            "name": name,
            "full_name": f"{org}/{name}",
            "owner_login": org,
            "private": visibility == "private",
            "html_url": f"https://github.com/{org}/{name}",
            "ssh_url": f"git@github.com:{org}/{name}.git",
        }

    def list_repositories(self, org: str | None = None, include_archived: bool = False) -> list[dict[str, object]]:
        _FakeGitHubService.last_list_call = {
            "org": org,
            "include_archived": include_archived,
        }
        return [
            {
                "id": 10,
                "name": "service-a",
                "full_name": "token-user/service-a",
                "owner_login": "token-user",
                "private": True,
                "archived": False,
                "default_branch": "main",
                "html_url": "https://github.com/token-user/service-a",
                "ssh_url": "git@github.com:token-user/service-a.git",
            }
        ]

    def get_authenticated_user_info(self) -> dict[str, str]:
        _FakeGitHubService.user_info_calls += 1
        return {
            "login": "example-user",
            "name": "Example User",
            "html_url": "http://github.com/example-user",
        }

    def delete_repositories(self, org: str, include: list[str] | None = None, exclude: list[str] | None = None, delete_all: bool = False, confirmation_phrase: str = "") -> dict[str, object]:
        _FakeGitHubService.last_delete_call = {
            "org": org,
            "include": include,
            "exclude": exclude,
            "delete_all": delete_all,
            "confirmation_phrase": confirmation_phrase,
        }
        return {
            "org": org,
            "deleted_repositories": ["other/hape-vibes/service-a"],
            "deleted_count": 1,
        }


def _build_test_client(monkeypatch, tmp_path, rate_limit: int = 10) -> TestClient:
    tokens_file = tmp_path / "api-tokens.json"
    monkeypatch.setattr("api.app.Config.get_api_tokens_file_path", lambda: str(tokens_file))
    monkeypatch.setattr("api.app.Config.get_api_rate_limit_per_minute", lambda: rate_limit)
    monkeypatch.setattr("api.app.Config.get_api_admin_key", lambda: "admin-key")
    monkeypatch.setattr("api.app.Config.get_github_provider_sqlite_path", lambda: str(tmp_path / "github-provider.sqlite"))
    from api.app import create_app

    app = create_app()
    return TestClient(app)


def test_protected_endpoint_requires_bearer_token(monkeypatch, tmp_path) -> None:
    client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path)
    response = client.post("/config/init-config-file", json={"config_file_path": str(tmp_path / "config.json")})
    assert response.status_code == 401


def test_token_auth_and_rate_limit(monkeypatch, tmp_path) -> None:
    client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path, rate_limit=2)
    token_response = client.post(
        "/auth/tokens",
        headers={"X-Hape-Admin-Key": "admin-key"},
        json={"name": "test-token"},
    )
    assert token_response.status_code == 200
    token = token_response.json()["token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    first_response = client.post("/config/init-config-file", headers=auth_headers, json={"config_file_path": str(tmp_path / "cfg-1.json")})
    second_response = client.post("/config/init-config-file", headers=auth_headers, json={"config_file_path": str(tmp_path / "cfg-2.json")})
    third_response = client.post("/config/init-config-file", headers=auth_headers, json={"config_file_path": str(tmp_path / "cfg-3.json")})

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert third_response.status_code == 429


def test_cli_api_parity_routes_exist(monkeypatch, tmp_path) -> None:
    client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path)
    route_paths = set(client.app.openapi()["paths"].keys())
    expected_paths = {
        "/config/init-config-file",
        "/config/show",
        "/gitlab/clone",
        "/gitlab/mr-count-per-day",
        "/github/init-repo",
        "/github/create/repo",
        "/github/list-repos",
        "/github/user-info",
        "/github/delete-repos",
        "/github/v1/installations/setup-url",
        "/github/v1/installations/verify",
        "/github/v1/installations/{installationId}/status",
        "/github/v1/repositories/discover",
        "/github/v1/revisions/resolve",
        "/github/v1/snapshots/read",
        "/github/v1/repositories",
        "/github/v1/commits/baseline",
        "/github/v1/commits/artifact",
        "/github/v1/tags",
        "/github/v1/repositories/dispose",
        "/github/v1/receipts/{receiptId}",
        "/github/v2/managed-destinations/{destination_id}/status",
        "/github/v2/managed-targets/setup-url",
        "/github/v2/managed-targets/verify",
        "/github/v2/managed-targets/{target_binding_id}/status",
        "/github/v2/managed-repositories",
        "/github/v2/managed-repositories/{repository_id}/commits/baseline",
        "/github/v2/managed-repositories/{repository_id}/commits/artifact",
        "/github/v2/managed-repositories/{repository_id}/tags",
        "/github/v2/managed-repositories/{repository_id}/dispose",
        "/github/v2/provider-operations/{operation_id}",
        "/github/v2/provider-receipts/{receipt_id}",
        "/jira/md-to-comment",
        "/confluence/get-page",
        "/confluence/create-page",
        "/confluence/md-to-page",
        "/csv/from-json",
        "/csv/to-json",
        "/markdown/export-tables-to-csv",
        "/markdown/import-csv-table",
        "/dora/validate-config",
        "/dora/list-projects",
        "/dora/list-deployments",
        "/dora/compute-project",
        "/eks-deployment-cost/report",
        "/kube-agent/investigate/pod",
        "/kube-agent/investigate/deployment",
        "/kube-agent/investigate/node",
        "/kube-agent/investigate/alert",
        "/kube-agent/cost-analyze",
        "/kube-agent/incidents/list",
        "/kube-agent/incidents/show",
        "/init-cicd",
        "/vault/kv-get",
    }
    missing_paths = expected_paths - route_paths
    assert not missing_paths


def test_github_create_repo_route_returns_service_payload(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("api.routers.github_router.GitHubService", _FakeGitHubService)
    client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path)
    token_response = client.post(
        "/auth/tokens",
        headers={"X-Hape-Admin-Key": "admin-key"},
        json={"name": "test-token"},
    )
    assert token_response.status_code == 200
    token = token_response.json()["token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/github/create/repo",
        headers=auth_headers,
        json={"org": "hape-vibes", "name": "service-a", "visibility": "public"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert _FakeGitHubService.last_create_call == {
        "org": "hape-vibes",
        "name": "service-a",
        "visibility": "public",
    }
    assert payload["full_name"] == "hape-vibes/service-a"
    assert payload["private"] is False


def test_github_create_repo_route_defaults_to_private_visibility(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("api.routers.github_router.GitHubService", _FakeGitHubService)
    client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path)
    token_response = client.post(
        "/auth/tokens",
        headers={"X-Hape-Admin-Key": "admin-key"},
        json={"name": "test-token"},
    )
    assert token_response.status_code == 200
    token = token_response.json()["token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/github/create/repo",
        headers=auth_headers,
        json={"org": "hape-vibes", "name": "service-a"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert _FakeGitHubService.last_create_call == {
        "org": "hape-vibes",
        "name": "service-a",
        "visibility": "private",
    }
    assert payload["private"] is True


def test_github_create_repo_route_rejects_invalid_visibility(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("api.routers.github_router.GitHubService", _FakeGitHubService)
    client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path)
    token_response = client.post(
        "/auth/tokens",
        headers={"X-Hape-Admin-Key": "admin-key"},
        json={"name": "test-token"},
    )
    assert token_response.status_code == 200
    token = token_response.json()["token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/github/create/repo",
        headers=auth_headers,
        json={"org": "hape-vibes", "name": "service-a", "visibility": "internal"},
    )
    assert response.status_code == 422


def test_github_list_repos_route_returns_service_payload(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("api.routers.github_router.GitHubService", _FakeGitHubService)
    client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path)
    token_response = client.post(
        "/auth/tokens",
        headers={"X-Hape-Admin-Key": "admin-key"},
        json={"name": "test-token"},
    )
    assert token_response.status_code == 200
    token = token_response.json()["token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/github/list-repos",
        headers=auth_headers,
        json={"org": "hape-vibes", "include_archived": True},
    )
    assert response.status_code == 200
    payload = response.json()
    assert _FakeGitHubService.last_list_call == {
        "org": "hape-vibes",
        "include_archived": True,
    }
    assert isinstance(payload, list)
    assert payload[0]["full_name"] == "token-user/service-a"
    assert payload[0]["owner_login"] == "token-user"


def test_github_list_repos_route_defaults_to_user_context_without_org(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("api.routers.github_router.GitHubService", _FakeGitHubService)
    client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path)
    token_response = client.post(
        "/auth/tokens",
        headers={"X-Hape-Admin-Key": "admin-key"},
        json={"name": "test-token"},
    )
    assert token_response.status_code == 200
    token = token_response.json()["token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/github/list-repos",
        headers=auth_headers,
        json={},
    )
    assert response.status_code == 200
    assert _FakeGitHubService.last_list_call == {
        "org": None,
        "include_archived": False,
    }


def test_github_user_info_route_returns_service_payload(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("api.routers.github_router.GitHubService", _FakeGitHubService)
    client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path)
    token_response = client.post(
        "/auth/tokens",
        headers={"X-Hape-Admin-Key": "admin-key"},
        json={"name": "test-token"},
    )
    assert token_response.status_code == 200
    token = token_response.json()["token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/github/user-info", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert _FakeGitHubService.user_info_calls >= 1
    assert payload == {
        "login": "example-user",
        "name": "Example User",
        "html_url": "http://github.com/example-user",
    }


def test_github_delete_repos_route_returns_service_payload(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("api.routers.github_router.GitHubService", _FakeGitHubService)
    client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path)
    token_response = client.post(
        "/auth/tokens",
        headers={"X-Hape-Admin-Key": "admin-key"},
        json={"name": "test-token"},
    )
    assert token_response.status_code == 200
    token = token_response.json()["token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/github/delete-repos",
        headers=auth_headers,
        json={
            "org": "hape-vibes",
            "include": ["service-a"],
            "exclude": ["service-b"],
            "delete_all": True,
            "confirmation_phrase": "delete selected repos",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert _FakeGitHubService.last_delete_call == {
        "org": "hape-vibes",
        "include": ["service-a"],
        "exclude": ["service-b"],
        "delete_all": True,
        "confirmation_phrase": "delete selected repos",
    }
    assert payload["deleted_count"] == 1


SOURCE_OPERATIONS = [
    "installation.setup_url",
    "installation.verify",
    "installation.status",
    "repository.discover",
    "revision.resolve",
    "snapshot.read",
    "receipt.get",
]
MANAGED_OPERATIONS = [
    "repository.create_private",
    "commit.publish_baseline",
    "commit.publish_artifact",
    "tag.publish_annotated",
    "repository.dispose",
    "receipt.get",
]
LEGACY_ROUTES = [
    ("/github/init-repo", {"repo_path": "/tmp/example"}),
    ("/github/create/repo", {"org": "example-org", "name": "service-a"}),
    ("/github/list-repos", {"org": "example-org"}),
    ("/github/user-info", None),
    ("/github/delete-repos", {"org": "example-org", "confirmation_phrase": "delete selected repos"}),
]


def _product_headers(client: TestClient, role: str, operations: list[str]) -> dict[str, str]:
    created = client.app.state.token_service.create_token(name=role, credential_role=role, allowed_operations=operations)
    return {"Authorization": f"Bearer {created['token']}"}


def test_product_tokens_are_denied_on_legacy_github_routes(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("api.routers.github_router.GitHubService", _FakeGitHubService)
    client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path)
    for role, operations in (("source-read", SOURCE_OPERATIONS), ("managed-write", MANAGED_OPERATIONS)):
        headers = _product_headers(client, role, operations)
        for path, body in LEGACY_ROUTES:
            response = client.post(path, headers=headers, json=body or {})
            assert response.status_code == 403
            assert response.json()["detail"]["code"] == "policy_denied"


def test_new_github_routes_require_exact_operation_claim(monkeypatch, tmp_path) -> None:
    client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path)
    source_headers = _product_headers(client, "source-read", SOURCE_OPERATIONS)
    managed_headers = _product_headers(client, "managed-write", MANAGED_OPERATIONS)
    create_body = {
        "idempotencyKey": "k1",
        "grant": {
            "grantId": "g1",
            "iss": "hape-platform-agent-authorization",
            "aud": "hape-framework",
            "sub": "hape-platform-agent-backend",
            "tenantId": "11111111-1111-1111-1111-111111111111",
            "appId": "33333333-3333-3333-3333-333333333333",
            "operation": "repository.create_private",
            "resourceConstraints": {},
            "inputDigest": "abc",
            "nonce": "n1",
            "iat": 1,
            "exp": 301,
            "decisionId": "d1",
        },
    }
    denied = client.post("/github/v1/repositories", headers=source_headers, json=create_body)
    assert denied.status_code == 403
    assert denied.json()["detail"]["code"] == "policy_denied"
    snapshot_body = dict(create_body)
    snapshot_body["grant"] = dict(create_body["grant"])
    snapshot_body["grant"]["operation"] = "snapshot.read"
    denied_managed = client.post("/github/v1/snapshots/read", headers=managed_headers, json=snapshot_body)
    assert denied_managed.status_code == 403
    assert denied_managed.json()["detail"]["code"] == "policy_denied"
    missing_claim = _product_headers(client, "source-read", ["receipt.get"])
    denied_missing = client.post("/github/v1/snapshots/read", headers=missing_claim, json=snapshot_body)
    assert denied_missing.status_code == 403


def test_admin_can_mint_exactly_one_product_role(monkeypatch, tmp_path) -> None:
    from datetime import datetime, timezone

    from api.auth.token_service import ApiTokenService

    client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path)
    both_roles = client.post(
        "/auth/tokens",
        headers={"X-Hape-Admin-Key": "admin-key"},
        json={"name": "invalid", "credential_role": "source-read,managed-write"},
    )
    assert both_roles.status_code == 400
    unknown = client.post(
        "/auth/tokens",
        headers={"X-Hape-Admin-Key": "admin-key"},
        json={"name": "invalid", "credential_role": "operator"},
    )
    assert unknown.status_code == 400
    created = client.post(
        "/auth/tokens",
        headers={"X-Hape-Admin-Key": "admin-key"},
        json={"name": "source-caller", "credential_role": "source-read"},
    )
    assert created.status_code == 200
    payload = created.json()
    assert payload["credential_role"] == "source-read"
    assert payload["jti"]
    claims = client.app.state.token_service.validate_token(payload["token"])
    assert claims is not None
    assert claims["allowed_operations"] == sorted(SOURCE_OPERATIONS)
    assert claims["exp"] - claims["iat"] == ApiTokenService.PRODUCT_CALLER_TTL_SECONDS
    assert claims["exp"] > int(datetime.now(timezone.utc).timestamp())
    managed = client.post(
        "/auth/tokens",
        headers={"X-Hape-Admin-Key": "admin-key"},
        json={"name": "managed-caller", "credential_role": "managed-write"},
    )
    assert managed.status_code == 200
    managed_claims = client.app.state.token_service.validate_token(managed.json()["token"])
    assert managed_claims is not None
    assert managed_claims["allowed_operations"] == sorted(MANAGED_OPERATIONS)


def test_admin_source_read_token_cannot_call_managed_routes(monkeypatch, tmp_path) -> None:
    from tests.github.test_github_app_service import _grant, _service, _source_bindings

    service, _fixture = _service()
    client = _build_test_client(monkeypatch=monkeypatch, tmp_path=tmp_path)
    client.app.state.github_app_service = service
    minted = client.post(
        "/auth/tokens",
        headers={"X-Hape-Admin-Key": "admin-key"},
        json={"name": "source-caller", "credential_role": "source-read"},
    )
    headers = {"Authorization": f"Bearer {minted.json()['token']}"}
    setup = client.post(
        "/github/v1/installations/setup-url",
        headers=headers,
        json={"idempotencyKey": "admin-setup", "grant": _grant("installation.setup_url", _source_bindings(), nonce="admin-s")},
    )
    assert setup.status_code == 200
    denied = client.post(
        "/github/v1/repositories",
        headers=headers,
        json={"idempotencyKey": "admin-create", "grant": _grant("repository.create_private", {"installationId": 101}, nonce="admin-c")},
    )
    assert denied.status_code == 403
    assert denied.json()["detail"]["code"] == "policy_denied"
