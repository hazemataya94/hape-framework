import argparse
import json

import cli.commands.github_commands as github_commands_module
from cli.commands.github_commands import GitHubCommands


class _FakeGitHubService:
    last_call = {}
    last_list_call = {}
    user_info_calls = 0
    last_delete_preview_call = {}
    last_delete_call = {}

    def init_repo(self, repo_path: str, owner: str | None = None, name: str | None = None, visibility: str = "private") -> dict[str, str]:
        _FakeGitHubService.last_call = {
            "repo_path": repo_path,
            "owner": owner,
            "name": name,
            "visibility": visibility,
        }
        return {
            "full_name": "hape-vibes/service-a",
            "html_url": "https://github.com/hape-vibes/service-a",
            "clone_url": "git@github.com:hape-vibes/service-a.git",
            "local_path": repo_path,
            "admin_login": "host-admin",
        }

    def list_repositories(self, org: str | None = None, include_archived: bool = False) -> list[dict[str, object]]:
        _FakeGitHubService.last_list_call = {
            "org": org,
            "include_archived": include_archived,
        }
        return [
            {
                "id": 21,
                "name": "service-a",
                "full_name": "hape-vibes/service-a",
                "owner_login": "hape-vibes",
                "private": True,
                "archived": False,
                "default_branch": "main",
                "html_url": "https://github.com/hape-vibes/service-a",
                "ssh_url": "git@github.com:hape-vibes/service-a.git",
            }
        ]

    def get_authenticated_user_info(self) -> dict[str, str]:
        _FakeGitHubService.user_info_calls += 1
        return {
            "login": "hazemataya94",
            "name": "Hazem Ataya",
            "html_url": "http://github.com/hazemataya94",
        }

    def list_repositories_for_deletion(self, org: str, include: list[str] | None = None, exclude: list[str] | None = None, delete_all: bool = False) -> list[dict[str, object]]:
        _FakeGitHubService.last_delete_preview_call = {
            "org": org,
            "include": include,
            "exclude": exclude,
            "delete_all": delete_all,
        }
        return [
            {
                "name": "service-a",
                "full_name": "hape-vibes/service-a",
                "private": True,
                "archived": False,
                "html_url": "https://github.com/hape-vibes/service-a",
            }
        ]

    def get_delete_repositories_confirmation_phrase(self) -> str:
        return "delete selected repos"

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


def test_init_repo_command_parses_and_calls_service(monkeypatch, capsys) -> None:
    monkeypatch.setattr(github_commands_module, "GitHubService", _FakeGitHubService)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    GitHubCommands.register(subparsers)
    args = parser.parse_args(
        [
            "github",
            "init-repo",
            "--repo-path",
            "/path/to/repo",
            "--owner",
            "hape-vibes",
            "--name",
            "service-a",
            "--public",
        ]
    )
    args.func(args)
    assert _FakeGitHubService.last_call == {
        "repo_path": "/path/to/repo",
        "owner": "hape-vibes",
        "name": "service-a",
        "visibility": "public",
    }
    output = capsys.readouterr().out
    assert "repository: hape-vibes/service-a" in output
    assert "admin_collaborator: host-admin" in output


def test_list_repos_command_parses_and_calls_service(monkeypatch, capsys) -> None:
    monkeypatch.setattr(github_commands_module, "GitHubService", _FakeGitHubService)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    GitHubCommands.register(subparsers)
    args = parser.parse_args(
        [
            "github",
            "list-repos",
            "--org",
            "hape-vibes",
            "--include-archived",
        ]
    )
    args.func(args)
    assert _FakeGitHubService.last_list_call == {
        "org": "hape-vibes",
        "include_archived": True,
    }
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload[0]["full_name"] == "hape-vibes/service-a"
    assert payload[0]["owner_login"] == "hape-vibes"


def test_list_repos_command_defaults_to_user_context_when_org_is_not_passed(monkeypatch, capsys) -> None:
    monkeypatch.setattr(github_commands_module, "GitHubService", _FakeGitHubService)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    GitHubCommands.register(subparsers)
    args = parser.parse_args(
        [
            "github",
            "list-repos",
        ]
    )
    args.func(args)
    assert _FakeGitHubService.last_list_call == {
        "org": None,
        "include_archived": False,
    }
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload[0]["full_name"] == "hape-vibes/service-a"


def test_user_info_command_calls_service_and_prints_json(monkeypatch, capsys) -> None:
    monkeypatch.setattr(github_commands_module, "GitHubService", _FakeGitHubService)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    GitHubCommands.register(subparsers)
    args = parser.parse_args(
        [
            "github",
            "user-info",
        ]
    )
    args.func(args)
    assert _FakeGitHubService.user_info_calls >= 1
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["login"] == "hazemataya94"
    assert payload["html_url"] == "http://github.com/hazemataya94"


def test_delete_repos_command_previews_and_deletes_after_confirmation(monkeypatch, capsys) -> None:
    monkeypatch.setattr(github_commands_module, "GitHubService", _FakeGitHubService)
    monkeypatch.setattr("builtins.input", lambda _: "delete selected repos")
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    GitHubCommands.register(subparsers)
    args = parser.parse_args(
        [
            "github",
            "delete-repos",
            "--org",
            "hape-vibes",
            "--all",
            "--exclude",
            "service-b",
        ]
    )
    args.func(args)
    assert _FakeGitHubService.last_delete_preview_call == {
        "org": "hape-vibes",
        "include": None,
        "exclude": ["service-b"],
        "delete_all": True,
    }
    assert _FakeGitHubService.last_delete_call == {
        "org": "hape-vibes",
        "include": None,
        "exclude": ["service-b"],
        "delete_all": True,
        "confirmation_phrase": "delete selected repos",
    }
    output = capsys.readouterr().out
    assert "Repositories scheduled for deletion:" in output
    assert "hape-vibes/service-a" in output
    assert '"deleted_count": 1' in output


def test_delete_repos_command_cancels_when_confirmation_phrase_mismatches(monkeypatch, capsys) -> None:
    monkeypatch.setattr(github_commands_module, "GitHubService", _FakeGitHubService)
    _FakeGitHubService.last_delete_call = {}
    monkeypatch.setattr("builtins.input", lambda _: "nope")
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    GitHubCommands.register(subparsers)
    args = parser.parse_args(
        [
            "github",
            "delete-repos",
            "--org",
            "hape-vibes",
            "--include",
            "service-a",
        ]
    )
    args.func(args)
    output = capsys.readouterr().out
    assert "Deletion cancelled." in output
    assert _FakeGitHubService.last_delete_call == {}


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__]))
