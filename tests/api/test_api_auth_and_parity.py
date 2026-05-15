from __future__ import annotations

from fastapi.testclient import TestClient


class _FakeGitHubService:
    last_list_call: dict[str, object] = {}
    user_info_calls: int = 0
    last_delete_call: dict[str, object] = {}

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
            "login": "hazemataya94",
            "name": "Hazem Ataya",
            "html_url": "http://github.com/hazemataya94",
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
            "deleted_repositories": ["hape-vibes/service-a"],
            "deleted_count": 1,
        }


def _build_test_client(monkeypatch, tmp_path, rate_limit: int = 10) -> TestClient:
    tokens_file = tmp_path / "api-tokens.json"
    monkeypatch.setattr("api.app.Config.get_api_tokens_file_path", lambda: str(tokens_file))
    monkeypatch.setattr("api.app.Config.get_api_rate_limit_per_minute", lambda: rate_limit)
    monkeypatch.setattr("api.app.Config.get_api_admin_key", lambda: "admin-key")
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
    route_paths = {route.path for route in client.app.routes}
    expected_paths = {
        "/config/init-config-file",
        "/gitlab/clone",
        "/gitlab/mr-count-per-day",
        "/github/init-repo",
        "/github/list-repos",
        "/github/user-info",
        "/github/delete-repos",
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
    }
    missing_paths = expected_paths - route_paths
    assert not missing_paths


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
        "login": "hazemataya94",
        "name": "Hazem Ataya",
        "html_url": "http://github.com/hazemataya94",
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
