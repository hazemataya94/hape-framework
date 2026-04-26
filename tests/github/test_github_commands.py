import argparse

import cli.commands.github_commands as github_commands_module
from cli.commands.github_commands import GitHubCommands


class _FakeGitHubService:
    last_call = {}

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


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__]))
