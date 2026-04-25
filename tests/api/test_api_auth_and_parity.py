from __future__ import annotations

from fastapi.testclient import TestClient


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
