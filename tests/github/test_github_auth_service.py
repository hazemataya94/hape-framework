import io
import json
import os
from pathlib import Path

import pytest

from core.errors.exceptions import HapeOperationError, HapeValidationError
from services.config_service import ConfigService
from services.github_auth_service import GitHubAuthService


class _FakeGitHubService:
    def get_authenticated_user_info(self) -> dict[str, str]:
        return {
            "login": "operator",
            "name": "Operator",
            "html_url": "https://github.com/operator",
        }

    def list_repositories(self, org: str | None = None, include_archived: bool = False) -> list[dict[str, str]]:
        return [{"full_name": f"{org}/demo", "name": "demo"}]


class _Result:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _install_command_fakes(monkeypatch, calls: list[list[str]], *, ssh_g_ok: bool = True, ssh_probe_ok: bool = True) -> None:
    monkeypatch.delenv("HAPE_GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("HAPE_GITHUB_DEFAULT_OWNER", raising=False)

    def fake_which(name: str) -> str | None:
        if name in {"gh", "ssh"}:
            return f"/usr/bin/{name}"
        return None

    def fake_run(*args, **kwargs):
        command = args[0]
        calls.append(command)
        binary = command[0]
        if binary.endswith("/ssh") or binary == "ssh":
            if "-G" in command:
                if not ssh_g_ok:
                    return _Result(1, "", "ssh config failed")
                return _Result(0, "hostname github.com\nuser git\nidentityfile /path/to/.ssh/custom_key\n")
            if "-T" in command:
                if ssh_probe_ok:
                    return _Result(1, "", "Hi operator! You've successfully authenticated")
                return _Result(255, "", "Permission denied (publickey).")
            return _Result(1, "")
        if command[1:3] == ["auth", "login"]:
            return _Result(0)
        if command[1:3] == ["auth", "token"]:
            return _Result(0, "ghp_from_gh\n")
        return _Result(1, "")

    fake_stdin = io.StringIO()
    fake_stdin.isatty = lambda: True  # type: ignore[method-assign]
    monkeypatch.setattr("services.github_auth_service.shutil.which", fake_which)
    monkeypatch.setattr("services.github_auth_service.subprocess.run", fake_run)
    monkeypatch.setattr("services.github_auth_service.sys.stdin", fake_stdin)


def test_configure_owner_stores_default_owner(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    github_auth_service = GitHubAuthService(config_service=ConfigService())
    result = github_auth_service.configure_owner(owner="example-org", config_path=str(config_path))
    assert result["owner"] == "example-org"
    stored = json.loads(config_path.read_text(encoding="utf-8"))
    assert stored["HAPE_GITHUB_DEFAULT_OWNER"] == "example-org"


def test_login_with_token_stores_token(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    github_auth_service = GitHubAuthService(config_service=ConfigService())
    result = github_auth_service.login_with_token(token="  ghp_example_token  \n", config_path=str(config_path))
    assert result["method"] == "token-stdin"
    assert result["token_stored"] is True
    stored = json.loads(config_path.read_text(encoding="utf-8"))
    assert stored["HAPE_GITHUB_TOKEN"] == "ghp_example_token"
    assert os.environ.get("HAPE_GITHUB_TOKEN") == "ghp_example_token"


def test_store_token_syncs_existing_dotenv_key(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("HAPE_GITHUB_TOKEN=stale_token\nOTHER=1\n", encoding="utf-8")
    monkeypatch.setattr("core.config.Config.default_dotenv_path", dotenv_path)
    monkeypatch.delenv("HAPE_GITHUB_TOKEN", raising=False)
    github_auth_service = GitHubAuthService(config_service=ConfigService())
    result = github_auth_service.login_with_token(token="ghp_fresh", config_path=str(config_path))
    assert result["method"] == "token-stdin"
    assert dotenv_path.read_text(encoding="utf-8") == "HAPE_GITHUB_TOKEN=ghp_fresh\nOTHER=1\n"
    assert os.environ.get("HAPE_GITHUB_TOKEN") == "ghp_fresh"


def test_login_with_gh_defaults_to_interactive_auth_login(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    calls: list[list[str]] = []
    _install_command_fakes(monkeypatch, calls)
    github_auth_service = GitHubAuthService(config_service=ConfigService())
    result = github_auth_service.login_with_gh(config_path=str(config_path))
    assert result["method"] == "gh"
    assert result["interactive"] is True
    login_calls = [call for call in calls if len(call) > 2 and call[1:3] == ["auth", "login"]]
    assert login_calls == [["/usr/bin/gh", "auth", "login"]]


def test_login_with_gh_fixed_hostname_protocol_uses_ssh(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    calls: list[list[str]] = []
    _install_command_fakes(monkeypatch, calls)
    github_auth_service = GitHubAuthService(config_service=ConfigService())
    result = github_auth_service.login_with_gh(
        config_path=str(config_path),
        hostname="github.com",
        git_protocol="ssh",
    )
    assert result["git_protocol"] == "ssh"
    assert result["interactive"] is False
    login_calls = [call for call in calls if len(call) > 2 and call[1:3] == ["auth", "login"]]
    assert "--git-protocol" in login_calls[0]
    assert "ssh" in login_calls[0]
    assert "--hostname" in login_calls[0]
    assert "github.com" in login_calls[0]
    assert "--skip-ssh-key" in login_calls[0]


def test_bootstrap_requires_owner(tmp_path: Path) -> None:
    github_auth_service = GitHubAuthService(config_service=ConfigService())
    with pytest.raises(HapeValidationError) as exc_info:
        github_auth_service.bootstrap(owner=None, yes=True, config_path=str(tmp_path / "config.json"))
    assert exc_info.value.code == "GITHUB_AUTH_OWNER_REQUIRED"


def test_bootstrap_cancelled_before_writes(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    calls: list[list[str]] = []
    _install_command_fakes(monkeypatch, calls)
    github_auth_service = GitHubAuthService(
        config_service=ConfigService(),
        github_service=_FakeGitHubService(),  # type: ignore[arg-type]
        input_func=lambda _prompt: "n",
    )
    with pytest.raises(HapeValidationError) as exc_info:
        github_auth_service.bootstrap(owner="example-org", config_path=str(config_path))
    assert exc_info.value.code == "GITHUB_AUTH_BOOTSTRAP_CANCELLED"
    assert not config_path.exists()
    assert not any(len(call) > 2 and call[1:3] == ["auth", "login"] for call in calls)


def test_bootstrap_yes_uses_ssh_defaults_and_writes(monkeypatch, tmp_path: Path, capsys) -> None:
    config_path = tmp_path / "config.json"
    calls: list[list[str]] = []
    _install_command_fakes(monkeypatch, calls)
    github_auth_service = GitHubAuthService(
        config_service=ConfigService(),
        github_service=_FakeGitHubService(),  # type: ignore[arg-type]
        input_func=lambda _prompt: (_ for _ in ()).throw(AssertionError("prompt should not be used")),
    )
    result = github_auth_service.bootstrap(owner="example-org", yes=True, config_path=str(config_path))
    assert result["owner"] == "example-org"
    assert result["hostname"] == "github.com"
    assert result["git_protocol"] == "ssh"
    assert result["status"]["auth_ok"] is True
    assert result["plan"]["ssh_preflight"]["resolved"]["identity_files"] == ["/path/to/.ssh/custom_key"]
    stored = json.loads(config_path.read_text(encoding="utf-8"))
    assert stored["HAPE_GITHUB_DEFAULT_OWNER"] == "example-org"
    assert stored["HAPE_GITHUB_TOKEN"] == "ghp_from_gh"
    assert "Bootstrap plan" in capsys.readouterr().out
    assert any(call[:2] == ["/usr/bin/ssh", "-G"] for call in calls)
    # Existing gh session token is reused; do not force another auth login.
    assert not any(len(call) > 2 and call[1:3] == ["auth", "login"] for call in calls)
    assert any(len(call) > 2 and call[1:3] == ["auth", "token"] for call in calls)


def test_bootstrap_falls_back_to_login_when_gh_session_missing(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    calls: list[list[str]] = []
    token_calls = {"count": 0}

    def fake_which(name: str) -> str | None:
        if name in {"gh", "ssh"}:
            return f"/usr/bin/{name}"
        return None

    def fake_run_ordered(*args, **kwargs):
        command = args[0]
        calls.append(command)
        binary = command[0]
        if binary.endswith("/ssh") or binary == "ssh":
            if "-G" in command:
                return _Result(0, "hostname github.com\nuser git\nidentityfile /path/to/.ssh/custom_key\n")
            if "-T" in command:
                return _Result(1, "", "Hi operator! You've successfully authenticated")
            return _Result(1, "")
        if command[1:3] == ["auth", "token"]:
            token_calls["count"] += 1
            if token_calls["count"] == 1:
                return _Result(1, "", "not logged in")
            return _Result(0, "ghp_after_login\n")
        if command[1:3] == ["auth", "login"]:
            return _Result(0)
        return _Result(1, "")

    monkeypatch.delenv("HAPE_GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("HAPE_GITHUB_DEFAULT_OWNER", raising=False)
    monkeypatch.setattr("services.github_auth_service.shutil.which", fake_which)
    monkeypatch.setattr("services.github_auth_service.subprocess.run", fake_run_ordered)
    github_auth_service = GitHubAuthService(
        config_service=ConfigService(),
        github_service=_FakeGitHubService(),  # type: ignore[arg-type]
    )
    result = github_auth_service.bootstrap(owner="example-org", yes=True, config_path=str(config_path))
    assert result["login"]["method"] == "gh"
    assert any(len(call) > 2 and call[1:3] == ["auth", "login"] for call in calls)
    stored = json.loads(config_path.read_text(encoding="utf-8"))
    assert stored["HAPE_GITHUB_TOKEN"] == "ghp_after_login"


def test_bootstrap_set_github_auth_method_prompts_protocol(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    calls: list[list[str]] = []
    _install_command_fakes(monkeypatch, calls)
    responses = iter(["https"])
    github_auth_service = GitHubAuthService(
        config_service=ConfigService(),
        github_service=_FakeGitHubService(),  # type: ignore[arg-type]
        input_func=lambda _prompt: next(responses),
    )
    result = github_auth_service.bootstrap(
        owner="example-org",
        yes=True,
        set_github_auth_method=True,
        config_path=str(config_path),
    )
    assert result["git_protocol"] == "https"
    assert result["plan"]["ssh_preflight"] is None
    assert not any(call[:2] == ["/usr/bin/ssh", "-G"] for call in calls)


def test_bootstrap_ssh_config_unresolved_fails_before_login(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    calls: list[list[str]] = []
    _install_command_fakes(monkeypatch, calls, ssh_g_ok=False)
    github_auth_service = GitHubAuthService(config_service=ConfigService(), github_service=_FakeGitHubService())  # type: ignore[arg-type]
    with pytest.raises(HapeOperationError) as exc_info:
        github_auth_service.bootstrap(owner="example-org", yes=True, config_path=str(config_path))
    assert exc_info.value.code == "GITHUB_AUTH_SSH_CONFIG_UNRESOLVED"
    assert not any(len(call) > 2 and call[1:3] == ["auth", "login"] for call in calls)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
