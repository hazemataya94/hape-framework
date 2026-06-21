from pathlib import Path

import pytest
import requests

from core.errors.exceptions import HapeExternalError, HapeValidationError
from services.github_service import GitHubService


class _FakeGitHubClient:
    created_payloads: list[dict[str, object]] = []
    added_collaborators: list[dict[str, object]] = []

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

    def create_organization_repository(self, org_name: str, repo_name: str, private: bool = True) -> dict[str, str]:
        self.created_payloads.append(
            {
                "org_name": org_name,
                "repo_name": repo_name,
                "private": private,
            }
        )
        return {
            "full_name": f"{org_name}/{repo_name}",
            "html_url": f"https://github.com/{org_name}/{repo_name}",
            "ssh_url": f"git@github.com:{org_name}/{repo_name}.git",
        }

    def resolve_token_default_owner(self) -> str:
        return "token-user"

    def resolve_user_login_by_email(self, email: str) -> str:
        return "host-admin"

    def add_repository_collaborator(self, owner: str, repo_name: str, username: str, permission: str = "push") -> bool:
        self.added_collaborators.append(
            {
                "owner": owner,
                "repo_name": repo_name,
                "username": username,
                "permission": permission,
            }
        )
        return True


class _FakeFailingGitHubClient:
    def create_repository(self, owner: str, repo_name: str, private: bool = True) -> dict[str, str]:
        response = requests.Response()
        response.status_code = 422
        response._content = b'{"message":"Validation Failed","errors":[{"field":"name","code":"already_exists"}]}'
        raise requests.HTTPError("422 Client Error", response=response)

    def create_organization_repository(self, org_name: str, repo_name: str, private: bool = True) -> dict[str, str]:
        response = requests.Response()
        response.status_code = 422
        response._content = b'{"message":"Validation Failed","errors":[{"field":"name","code":"already_exists"}]}'
        raise requests.HTTPError("422 Client Error", response=response)

    def resolve_token_default_owner(self) -> str:
        return "token-user"

    def resolve_user_login_by_email(self, email: str) -> str:
        return "host-admin"

    def add_repository_collaborator(self, owner: str, repo_name: str, username: str, permission: str = "push") -> bool:
        return True


class _FakeListRepositoriesGitHubClient:
    user_calls: list[dict[str, object]] = []
    org_calls: list[dict[str, object]] = []
    deleted_calls: list[dict[str, str]] = []

    def get_authenticated_user_repositories(self, include_archived: bool = False) -> list[dict[str, object]]:
        self.user_calls.append({"include_archived": include_archived})
        repositories = [
            {
                "id": 22,
                "name": "service-b",
                "full_name": "token-user/service-b",
                "owner": {"login": "token-user"},
                "private": False,
                "archived": False,
                "default_branch": "main",
                "html_url": "https://github.com/token-user/service-b",
                "ssh_url": "git@github.com:token-user/service-b.git",
            },
            {
                "id": 21,
                "name": "service-a",
                "full_name": "token-user/service-a",
                "owner": {"login": "token-user"},
                "private": True,
                "archived": False,
                "default_branch": "main",
                "html_url": "https://github.com/token-user/service-a",
                "ssh_url": "git@github.com:token-user/service-a.git",
            },
        ]
        return repositories

    def get_org_repositories(self, org_name: str, include_archived: bool = False) -> list[dict[str, object]]:
        self.org_calls.append({"org_name": org_name, "include_archived": include_archived})
        return [
            {
                "id": 31,
                "name": "service-c",
                "full_name": f"{org_name}/service-c",
                "owner": {"login": org_name},
                "private": True,
                "archived": bool(include_archived),
                "default_branch": "main",
                "html_url": f"https://github.com/{org_name}/service-c",
                "ssh_url": f"git@github.com:{org_name}/service-c.git",
            }
        ]

    def delete_repository(self, owner: str, repo_name: str) -> bool:
        self.deleted_calls.append({"owner": owner, "repo_name": repo_name})
        return True


class _FakeAuthenticatedUserGitHubClient:
    def get_authenticated_user(self) -> dict[str, str]:
        return {
            "login": "hazemataya94",
            "name": "Hazem Ataya",
            "html_url": "http://github.com/hazemataya94",
            "company": "example",
        }


class _FakeFailingAuthenticatedUserGitHubClient:
    def get_authenticated_user(self) -> dict[str, str]:
        raise RuntimeError("upstream error")


class _FakeFailingDeleteGitHubClient(_FakeListRepositoriesGitHubClient):
    def delete_repository(self, owner: str, repo_name: str) -> bool:
        raise RuntimeError("delete failed")


def test_create_repository_uses_private_default() -> None:
    service = GitHubService(github_client=_FakeGitHubClient())
    result = service.create_repository(org="hape-vibes", name="service-a")
    assert result == {
        "name": "service-a",
        "full_name": "hape-vibes/service-a",
        "owner_login": "hape-vibes",
        "private": True,
        "html_url": "https://github.com/hape-vibes/service-a",
        "ssh_url": "git@github.com:hape-vibes/service-a.git",
    }
    assert _FakeGitHubClient.created_payloads[-1] == {
        "org_name": "hape-vibes",
        "repo_name": "service-a",
        "private": True,
    }


def test_create_repository_supports_public_visibility() -> None:
    service = GitHubService(github_client=_FakeGitHubClient())
    result = service.create_repository(org="hape-vibes", name="service-a", visibility="public")
    assert result["private"] is False
    assert _FakeGitHubClient.created_payloads[-1] == {
        "org_name": "hape-vibes",
        "repo_name": "service-a",
        "private": False,
    }


def test_create_repository_requires_org() -> None:
    service = GitHubService(github_client=_FakeGitHubClient())
    with pytest.raises(HapeValidationError) as error:
        service.create_repository(org=" ", name="service-a")
    assert error.value.code == "GITHUB_CREATE_REPO_ORG_REQUIRED"


def test_create_repository_requires_name() -> None:
    service = GitHubService(github_client=_FakeGitHubClient())
    with pytest.raises(HapeValidationError) as error:
        service.create_repository(org="hape-vibes", name=" ")
    assert error.value.code == "GITHUB_CREATE_REPO_NAME_REQUIRED"


def test_create_repository_error_message_includes_github_reason() -> None:
    service = GitHubService(github_client=_FakeFailingGitHubClient())
    with pytest.raises(HapeExternalError) as error:
        service.create_repository(org="hape-vibes", name="service-a")
    assert error.value.code == "GITHUB_CREATE_REPO_FAILED"
    assert "status=422" in error.value.message
    assert "already_exists" in error.value.message


def test_init_repo_uses_repo_basename_and_private_default(tmp_path: Path, monkeypatch) -> None:
    repo_path = tmp_path / "service-a"
    repo_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("services.github_service.Config.get_github_default_owner", lambda: "")
    monkeypatch.setattr("services.github_service.GitHubService._run_git_init", lambda *args, **kwargs: None)
    monkeypatch.setattr("services.github_service.GitHubService._run_git_add_remote", lambda *args, **kwargs: None)
    monkeypatch.setattr("services.github_service.GitHubService._read_global_git_email", lambda *args, **kwargs: "admin@example.com")
    service = GitHubService(github_client=_FakeGitHubClient())
    result = service.init_repo(repo_path=str(repo_path))
    assert result["full_name"] == "token-user/service-a"
    assert result["local_path"] == str(repo_path.resolve())
    assert result["admin_login"] == "host-admin"
    assert _FakeGitHubClient.created_payloads[-1] == {
        "owner": "token-user",
        "repo_name": "service-a",
        "private": True,
    }
    assert _FakeGitHubClient.added_collaborators[-1] == {
        "owner": "token-user",
        "repo_name": "service-a",
        "username": "host-admin",
        "permission": "admin",
    }


def test_init_repo_prefers_configured_default_owner(tmp_path: Path, monkeypatch) -> None:
    repo_path = tmp_path / "service-b"
    repo_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("services.github_service.Config.get_github_default_owner", lambda: "hape-vibes")
    monkeypatch.setattr("services.github_service.GitHubService._run_git_init", lambda *args, **kwargs: None)
    monkeypatch.setattr("services.github_service.GitHubService._run_git_add_remote", lambda *args, **kwargs: None)
    monkeypatch.setattr("services.github_service.GitHubService._read_global_git_email", lambda *args, **kwargs: "admin@example.com")
    service = GitHubService(github_client=_FakeGitHubClient())
    result = service.init_repo(repo_path=str(repo_path), name="custom-name", visibility="public")
    assert result["full_name"] == "hape-vibes/custom-name"
    assert result["admin_login"] == "host-admin"
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
    monkeypatch.setattr("services.github_service.GitHubService._read_global_git_email", lambda *args, **kwargs: "admin@example.com")
    service = GitHubService(github_client=_FakeFailingGitHubClient())
    with pytest.raises(HapeExternalError) as error:
        service.init_repo(repo_path=str(repo_path))
    assert error.value.code == "GITHUB_CREATE_REPO_FAILED"
    assert "status=422" in error.value.message
    assert "already_exists" in error.value.message


def test_init_repo_fails_when_global_git_email_is_missing(tmp_path: Path, monkeypatch) -> None:
    repo_path = tmp_path / "service-e"
    repo_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("services.github_service.Config.get_github_default_owner", lambda: "")
    monkeypatch.setattr("services.github_service.GitHubService._run_git_init", lambda *args, **kwargs: None)
    monkeypatch.setattr("services.github_service.GitHubService._run_git_add_remote", lambda *args, **kwargs: None)
    monkeypatch.setattr("services.github_service.GitHubService._read_global_git_email", lambda *args, **kwargs: "")
    service = GitHubService(github_client=_FakeGitHubClient())
    with pytest.raises(HapeValidationError) as error:
        service.init_repo(repo_path=str(repo_path))
    assert error.value.code == "GITHUB_GLOBAL_GIT_EMAIL_UNAVAILABLE"


def test_list_repositories_for_user_scope_returns_sorted_payload() -> None:
    fake_client = _FakeListRepositoriesGitHubClient()
    service = GitHubService(github_client=fake_client)
    repositories = service.list_repositories()
    assert fake_client.user_calls[-1] == {"include_archived": False}
    assert repositories == [
        {
            "id": 21,
            "name": "service-a",
            "full_name": "token-user/service-a",
            "owner_login": "token-user",
            "private": True,
            "archived": False,
            "default_branch": "main",
            "html_url": "https://github.com/token-user/service-a",
            "ssh_url": "git@github.com:token-user/service-a.git",
        },
        {
            "id": 22,
            "name": "service-b",
            "full_name": "token-user/service-b",
            "owner_login": "token-user",
            "private": False,
            "archived": False,
            "default_branch": "main",
            "html_url": "https://github.com/token-user/service-b",
            "ssh_url": "git@github.com:token-user/service-b.git",
        },
    ]


def test_list_repositories_with_blank_org_uses_user_context() -> None:
    service = GitHubService(github_client=_FakeListRepositoriesGitHubClient())
    repositories = service.list_repositories(org="  ")
    assert repositories[0]["owner_login"] == "token-user"


def test_list_repositories_for_org_scope_calls_org_endpoint() -> None:
    fake_client = _FakeListRepositoriesGitHubClient()
    service = GitHubService(github_client=fake_client)
    repositories = service.list_repositories(org="hape-vibes", include_archived=True)
    assert fake_client.org_calls[-1] == {"org_name": "hape-vibes", "include_archived": True}
    assert repositories[0]["full_name"] == "hape-vibes/service-c"
    assert repositories[0]["archived"] is True


def test_clone_repositories_uses_list_repositories_and_clones_with_recursive_paths(tmp_path: Path, monkeypatch) -> None:
    service = GitHubService(github_client=_FakeListRepositoriesGitHubClient())
    list_repositories_calls: list[dict[str, object]] = []
    clone_calls: list[dict[str, str]] = []

    def _fake_list_repositories(org: str | None = None, include_archived: bool = False) -> list[dict[str, object]]:
        list_repositories_calls.append(
            {
                "org": org,
                "include_archived": include_archived,
            }
        )
        return [
            {
                "id": 21,
                "name": "service-a",
                "full_name": "microagi-labs/service-a",
                "owner_login": "microagi-labs",
                "private": True,
                "archived": False,
                "default_branch": "main",
                "html_url": "https://github.com/microagi-labs/service-a",
                "ssh_url": "git@github.com:microagi-labs/service-a.git",
            },
            {
                "id": 22,
                "name": "service-b",
                "full_name": "microagi-labs/service-b",
                "owner_login": "microagi-labs",
                "private": True,
                "archived": False,
                "default_branch": "main",
                "html_url": "https://github.com/microagi-labs/service-b",
                "ssh_url": "git@github.com:microagi-labs/service-b.git",
            },
        ]

    def _fake_run_git_clone(clone_url: str, target_path: Path) -> None:
        clone_calls.append({"clone_url": clone_url, "target_path": str(target_path)})

    monkeypatch.setattr(service, "list_repositories", _fake_list_repositories)
    monkeypatch.setattr(service, "_run_git_clone", _fake_run_git_clone)

    result = service.clone_repositories(org="microagi-labs", clone_dir=str(tmp_path))

    assert list_repositories_calls == [{"org": "microagi-labs", "include_archived": False}]
    assert clone_calls == [
        {
            "clone_url": "git@github.com:microagi-labs/service-a.git",
            "target_path": str(tmp_path / "microagi-labs" / "service-a"),
        },
        {
            "clone_url": "git@github.com:microagi-labs/service-b.git",
            "target_path": str(tmp_path / "microagi-labs" / "service-b"),
        },
    ]
    assert result["cloned_count"] == 2
    assert result["skipped_count"] == 0


def test_clone_repositories_skips_existing_repositories(tmp_path: Path, monkeypatch) -> None:
    service = GitHubService(github_client=_FakeListRepositoriesGitHubClient())
    existing_repository_path = tmp_path / "microagi-labs" / "service-a"
    existing_repository_path.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        service,
        "list_repositories",
        lambda org=None, include_archived=False: [
            {
                "id": 21,
                "name": "service-a",
                "full_name": "microagi-labs/service-a",
                "owner_login": "microagi-labs",
                "private": True,
                "archived": False,
                "default_branch": "main",
                "html_url": "https://github.com/microagi-labs/service-a",
                "ssh_url": "git@github.com:microagi-labs/service-a.git",
            },
            {
                "id": 22,
                "name": "service-b",
                "full_name": "microagi-labs/service-b",
                "owner_login": "microagi-labs",
                "private": True,
                "archived": False,
                "default_branch": "main",
                "html_url": "https://github.com/microagi-labs/service-b",
                "ssh_url": "git@github.com:microagi-labs/service-b.git",
            },
        ],
    )

    clone_calls: list[str] = []
    monkeypatch.setattr(service, "_run_git_clone", lambda clone_url, target_path: clone_calls.append(str(target_path)))

    result = service.clone_repositories(org="microagi-labs", clone_dir=str(tmp_path))

    assert clone_calls == [str(tmp_path / "microagi-labs" / "service-b")]
    assert result["cloned_count"] == 1
    assert result["skipped_count"] == 1
    assert result["skipped_repositories"] == ["microagi-labs/service-a"]


def test_clone_repositories_requires_org(tmp_path: Path) -> None:
    service = GitHubService(github_client=_FakeListRepositoriesGitHubClient())
    with pytest.raises(HapeValidationError) as error:
        service.clone_repositories(org="", clone_dir=str(tmp_path))
    assert error.value.code == "GITHUB_CLONE_REPOS_ORG_REQUIRED"


def test_clone_repositories_requires_clone_dir() -> None:
    service = GitHubService(github_client=_FakeListRepositoriesGitHubClient())
    with pytest.raises(HapeValidationError) as error:
        service.clone_repositories(org="microagi-labs", clone_dir="")
    assert error.value.code == "GITHUB_CLONE_REPOS_DIR_REQUIRED"


def test_get_authenticated_user_info_returns_normalized_payload() -> None:
    service = GitHubService(github_client=_FakeAuthenticatedUserGitHubClient())
    payload = service.get_authenticated_user_info()
    assert payload == {
        "login": "hazemataya94",
        "name": "Hazem Ataya",
        "html_url": "http://github.com/hazemataya94",
    }


def test_get_authenticated_user_info_handles_client_failure() -> None:
    service = GitHubService(github_client=_FakeFailingAuthenticatedUserGitHubClient())
    with pytest.raises(HapeExternalError) as error:
        service.get_authenticated_user_info()
    assert error.value.code == "GITHUB_AUTHENTICATED_USER_INFO_FAILED"


def test_list_repositories_for_deletion_requires_org() -> None:
    service = GitHubService(github_client=_FakeListRepositoriesGitHubClient())
    with pytest.raises(HapeValidationError) as error:
        service.list_repositories_for_deletion(org="")
    assert error.value.code == "GITHUB_DELETE_REPOS_ORG_REQUIRED"


def test_list_repositories_for_deletion_requires_selection() -> None:
    service = GitHubService(github_client=_FakeListRepositoriesGitHubClient())
    with pytest.raises(HapeValidationError) as error:
        service.list_repositories_for_deletion(org="hape-vibes")
    assert error.value.code == "GITHUB_DELETE_REPOS_SELECTION_REQUIRED"


def test_list_repositories_for_deletion_all_overrides_include_and_respects_exclude() -> None:
    fake_client = _FakeListRepositoriesGitHubClient()
    service = GitHubService(github_client=fake_client)
    repositories = service.list_repositories_for_deletion(
        org="hape-vibes",
        include=["service-does-not-matter"],
        exclude=["service-not-present"],
        delete_all=True,
    )
    assert repositories[0]["full_name"] == "hape-vibes/service-c"


def test_list_repositories_for_deletion_include_not_found() -> None:
    service = GitHubService(github_client=_FakeListRepositoriesGitHubClient())
    with pytest.raises(HapeValidationError) as error:
        service.list_repositories_for_deletion(org="hape-vibes", include=["missing-repo"])
    assert error.value.code == "GITHUB_DELETE_REPOS_INCLUDE_NOT_FOUND"


def test_list_repositories_for_deletion_fails_when_filters_leave_empty_set() -> None:
    service = GitHubService(github_client=_FakeListRepositoriesGitHubClient())
    with pytest.raises(HapeValidationError) as error:
        service.list_repositories_for_deletion(org="hape-vibes", delete_all=True, exclude=["service-c"])
    assert error.value.code == "GITHUB_DELETE_REPOS_EMPTY_AFTER_FILTERS"


def test_delete_repositories_requires_confirmation_phrase() -> None:
    service = GitHubService(github_client=_FakeListRepositoriesGitHubClient())
    with pytest.raises(HapeValidationError) as error:
        service.delete_repositories(org="hape-vibes", include=["service-c"], confirmation_phrase="wrong phrase")
    assert error.value.code == "GITHUB_DELETE_REPOS_CONFIRMATION_MISMATCH"


def test_delete_repositories_success() -> None:
    fake_client = _FakeListRepositoriesGitHubClient()
    service = GitHubService(github_client=fake_client)
    result = service.delete_repositories(
        org="hape-vibes",
        include=["service-c"],
        confirmation_phrase=service.get_delete_repositories_confirmation_phrase(),
    )
    assert fake_client.deleted_calls[-1] == {"owner": "hape-vibes", "repo_name": "service-c"}
    assert result["deleted_count"] == 1
    assert result["deleted_repositories"] == ["hape-vibes/service-c"]


def test_delete_repositories_handles_client_delete_failure() -> None:
    service = GitHubService(github_client=_FakeFailingDeleteGitHubClient())
    with pytest.raises(HapeExternalError) as error:
        service.delete_repositories(
            org="hape-vibes",
            include=["service-c"],
            confirmation_phrase=service.get_delete_repositories_confirmation_phrase(),
        )
    assert error.value.code == "GITHUB_DELETE_REPO_FAILED"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
