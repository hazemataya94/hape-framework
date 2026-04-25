from pathlib import Path

import pytest
import requests

from core.errors.exceptions import HapeExternalError, HapeValidationError
from services.github_service import GitHubService


class _FakeGitHubClient:
    created_payloads: list[dict[str, object]] = []

    def create_repository(self, owner: str, repo_name: str, private: bool = True) -> dict[str, str]:
        self.created_payloads.append(
            {
                "owner": owner,
                "repo_name": repo_name,
                "private": private,
            }
        )
        return {
            "full_name": f"{owner}/{repo_name}",
            "html_url": f"https://github.com/{owner}/{repo_name}",
            "ssh_url": f"git@github.com:{owner}/{repo_name}.git",
        }

    def resolve_token_default_owner(self) -> str:
        return "token-user"


class _FakeFailingGitHubClient:
    def create_repository(self, owner: str, repo_name: str, private: bool = True) -> dict[str, str]:
        response = requests.Response()
        response.status_code = 422
        response._content = b'{"message":"Validation Failed","errors":[{"field":"name","code":"already_exists"}]}'
        raise requests.HTTPError("422 Client Error", response=response)

    def resolve_token_default_owner(self) -> str:
        return "token-user"


def test_init_repo_uses_repo_basename_and_private_default(tmp_path: Path, monkeypatch) -> None:
    repo_path = tmp_path / "service-a"
    repo_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("services.github_service.Config.get_github_default_owner", lambda: "")
    monkeypatch.setattr("services.github_service.GitHubService._run_git_init", lambda *args, **kwargs: None)
    monkeypatch.setattr("services.github_service.GitHubService._run_git_add_remote", lambda *args, **kwargs: None)
    service = GitHubService(github_client=_FakeGitHubClient())
    result = service.init_repo(repo_path=str(repo_path))
    assert result["full_name"] == "token-user/service-a"
    assert result["local_path"] == str(repo_path.resolve())
    assert _FakeGitHubClient.created_payloads[-1] == {
        "owner": "token-user",
        "repo_name": "service-a",
        "private": True,
    }


def test_init_repo_prefers_configured_default_owner(tmp_path: Path, monkeypatch) -> None:
    repo_path = tmp_path / "service-b"
    repo_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("services.github_service.Config.get_github_default_owner", lambda: "hape-vibes")
    monkeypatch.setattr("services.github_service.GitHubService._run_git_init", lambda *args, **kwargs: None)
    monkeypatch.setattr("services.github_service.GitHubService._run_git_add_remote", lambda *args, **kwargs: None)
    service = GitHubService(github_client=_FakeGitHubClient())
    result = service.init_repo(repo_path=str(repo_path), name="custom-name", visibility="public")
    assert result["full_name"] == "hape-vibes/custom-name"
    assert _FakeGitHubClient.created_payloads[-1] == {
        "owner": "hape-vibes",
        "repo_name": "custom-name",
        "private": False,
    }


def test_init_repo_fails_when_git_directory_exists(tmp_path: Path, monkeypatch) -> None:
    repo_path = tmp_path / "service-c"
    (repo_path / ".git").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("services.github_service.Config.get_github_default_owner", lambda: "")
    service = GitHubService(github_client=_FakeGitHubClient())
    with pytest.raises(HapeValidationError) as error:
        service.init_repo(repo_path=str(repo_path))
    assert error.value.code == "GITHUB_REPO_ALREADY_INITIALIZED"


def test_init_repo_error_message_includes_github_reason(tmp_path: Path, monkeypatch) -> None:
    repo_path = tmp_path / "service-d"
    repo_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("services.github_service.Config.get_github_default_owner", lambda: "")
    service = GitHubService(github_client=_FakeFailingGitHubClient())
    with pytest.raises(HapeExternalError) as error:
        service.init_repo(repo_path=str(repo_path))
    assert error.value.code == "GITHUB_CREATE_REPO_FAILED"
    assert "status=422" in error.value.message
    assert "already_exists" in error.value.message


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
