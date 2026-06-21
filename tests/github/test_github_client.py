from typing import Any

import pytest

from clients.github_client import GitHubClient


def test_create_organization_repository_calls_org_endpoint(monkeypatch) -> None:
    captured_request: dict[str, Any] = {}

    def fake_request_json_post(self, endpoint_path: str, payload: dict[str, Any]) -> dict[str, Any]:
        captured_request["endpoint_path"] = endpoint_path
        captured_request["payload"] = payload
        return {
            "full_name": "example-org/service-a",
            "html_url": "https://github.com/example-org/service-a",
            "ssh_url": "git@github.com:example-org/service-a.git",
        }

    monkeypatch.setattr(GitHubClient, "_request_json_post", fake_request_json_post)
    github_client = GitHubClient(base_url="https://api.github.test", token="token")
    result = github_client.create_organization_repository(
        org_name="example-org",
        repo_name="service-a",
        private=False,
    )
    assert captured_request == {
        "endpoint_path": "/orgs/example-org/repos",
        "payload": {
            "name": "service-a",
            "private": False,
            "auto_init": False,
        },
    }
    assert result["full_name"] == "example-org/service-a"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
