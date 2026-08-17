import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from core.config import Config
from core.errors.exceptions import HapeOperationError, HapeValidationError
from core.errors.messages.github_error_messages import get_github_error_message
from core.logging import LocalLogging
from services.config_service import ConfigService
from services.github_service import GitHubService


class GitHubAuthService:
    DEFAULT_GH_SCOPES = "repo,read:org,admin:org"
    DEFAULT_OWNER = "hape-academy"
    DEFAULT_HOSTNAME = "github.com"
    DEFAULT_GIT_PROTOCOL = "ssh"
    GITHUB_TOKEN_KEY = "HAPE_GITHUB_TOKEN"
    GITHUB_DEFAULT_OWNER_KEY = "HAPE_GITHUB_DEFAULT_OWNER"
    AUTH_METHOD_GH = "1"
    AUTH_METHOD_TOKEN_STDIN = "2"

    def __init__(self, config_service: Optional[ConfigService] = None, github_service: Optional[GitHubService] = None, input_func: Optional[Callable[[str], str]] = None) -> None:
        self.config_service = config_service or ConfigService()
        self._github_service = github_service
        self.input_func = input_func or input
        self.logger = LocalLogging.get_logger("hape.github_auth_service")

    def _get_github_service(self) -> GitHubService:
        if self._github_service is None:
            self._github_service = GitHubService()
        return self._github_service

    def _require_gh_binary(self) -> str:
        gh_path = shutil.which("gh")
        if not gh_path:
            raise HapeOperationError(
                code="GITHUB_AUTH_GH_UNAVAILABLE",
                message=get_github_error_message("GITHUB_AUTH_GH_UNAVAILABLE"),
            )
        return gh_path

    def _require_ssh_binary(self) -> str:
        ssh_path = shutil.which("ssh")
        if not ssh_path:
            raise HapeOperationError(
                code="GITHUB_AUTH_SSH_UNAVAILABLE",
                message=get_github_error_message("GITHUB_AUTH_SSH_UNAVAILABLE"),
            )
        return ssh_path

    def _run_gh(self, args: list[str], *, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        gh_path = self._require_gh_binary()
        command = [gh_path, *args]
        self.logger.debug("running gh command: %s", " ".join(command))
        try:
            return subprocess.run(
                command,
                check=False,
                text=True,
                capture_output=capture_output,
                stdin=None if capture_output else sys.stdin,
                stdout=None if capture_output else sys.stdout,
                stderr=None if capture_output else sys.stderr,
            )
        except OSError as exc:
            raise HapeOperationError(
                code="GITHUB_AUTH_GH_UNAVAILABLE",
                message=get_github_error_message("GITHUB_AUTH_GH_UNAVAILABLE"),
            ) from exc

    def _run_ssh(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        ssh_path = self._require_ssh_binary()
        command = [ssh_path, *args]
        self.logger.debug("running ssh command: %s", " ".join(command))
        try:
            return subprocess.run(command, check=False, text=True, capture_output=True)
        except OSError as exc:
            raise HapeOperationError(
                code="GITHUB_AUTH_SSH_UNAVAILABLE",
                message=get_github_error_message("GITHUB_AUTH_SSH_UNAVAILABLE"),
            ) from exc

    def _sync_dotenv_token(self, token: str) -> bool:
        """Keep hape-framework/.env aligned when it already defines HAPE_GITHUB_TOKEN.

        Config prefers env/.env over config.json, so a stale dotenv value would
        shadow the token just written to config and make auth_ok false.
        """
        dotenv_path = Path(Config.default_dotenv_path)
        if not dotenv_path.exists():
            return False
        original = dotenv_path.read_text(encoding="utf-8")
        lines = original.splitlines(keepends=True)
        updated = False
        rewritten: list[str] = []
        key_prefix = f"{self.GITHUB_TOKEN_KEY}="
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith("#") or "=" not in line:
                rewritten.append(line)
                continue
            key = line.split("=", 1)[0].strip()
            if key != self.GITHUB_TOKEN_KEY:
                rewritten.append(line)
                continue
            newline = "\n" if line.endswith("\n") else ""
            rewritten.append(f"{key_prefix}{token}{newline}")
            updated = True
        if not updated:
            return False
        dotenv_path.write_text("".join(rewritten), encoding="utf-8")
        self.logger.info("synced %s in %s to match config.json", self.GITHUB_TOKEN_KEY, dotenv_path)
        return True

    def _store_token(self, token: str, config_path: Optional[str] = None) -> Dict[str, Any]:
        normalized_token = token.strip()
        if not normalized_token:
            raise HapeValidationError(
                code="GITHUB_AUTH_TOKEN_STDIN_EMPTY",
                message=get_github_error_message("GITHUB_AUTH_TOKEN_STDIN_EMPTY"),
            )
        store_result = self.config_service.set_config_value(
            key=self.GITHUB_TOKEN_KEY,
            value=normalized_token,
            config_path=config_path,
        )
        # Env and dotenv win over config.json; force the just-stored token into
        # the current process and sync dotenv when that file already defines it.
        os.environ[self.GITHUB_TOKEN_KEY] = normalized_token
        dotenv_synced = self._sync_dotenv_token(normalized_token)
        Config.reload_config()
        store_result["dotenv_synced"] = dotenv_synced
        return store_result

    def _token_configured(self) -> bool:
        try:
            token = Config.get_dora_github_token()
        except ValueError:
            return False
        return bool(token)

    def _prompt_line(self, message: str, default: str = "") -> str:
        suffix = f" [{default}]" if default else ""
        response = self.input_func(f"{message}{suffix}: ").strip()
        if response:
            return response
        return default

    def _prompt_yes_no(self, message: str, default_yes: bool = True) -> bool:
        default_label = "Y/n" if default_yes else "y/N"
        response = self.input_func(f"{message} [{default_label}]: ").strip().lower()
        if not response:
            return default_yes
        if response in {"y", "yes"}:
            return True
        if response in {"n", "no"}:
            return False
        return default_yes

    def _normalize_git_protocol(self, git_protocol: str) -> str:
        normalized = (git_protocol or "").strip().lower()
        if normalized not in {"ssh", "https"}:
            raise HapeValidationError(
                code="GITHUB_AUTH_GIT_PROTOCOL_INVALID",
                message=get_github_error_message("GITHUB_AUTH_GIT_PROTOCOL_INVALID", git_protocol=git_protocol),
            )
        return normalized

    def _resolve_git_protocol(self, git_protocol: Optional[str], set_github_auth_method: bool) -> str:
        if set_github_auth_method:
            selected = self._prompt_line("GitHub git protocol (ssh/https)", self.DEFAULT_GIT_PROTOCOL)
            return self._normalize_git_protocol(selected)
        if git_protocol:
            return self._normalize_git_protocol(git_protocol)
        return self.DEFAULT_GIT_PROTOCOL

    def _parse_ssh_g_output(self, output: str) -> Dict[str, Any]:
        resolved: Dict[str, Any] = {
            "hostname": None,
            "user": None,
            "identity_files": [],
        }
        for raw_line in output.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            key, value = parts[0].lower(), parts[1].strip()
            if key == "hostname":
                resolved["hostname"] = value
            elif key == "user":
                resolved["user"] = value
            elif key == "identityfile":
                resolved["identity_files"].append(value)
        return resolved

    def _preflight_ssh_config(self, hostname: str) -> Dict[str, Any]:
        target = f"git@{hostname}"
        resolve_result = self._run_ssh(["-G", target])
        if resolve_result.returncode != 0:
            raise HapeOperationError(
                code="GITHUB_AUTH_SSH_CONFIG_UNRESOLVED",
                message=get_github_error_message("GITHUB_AUTH_SSH_CONFIG_UNRESOLVED", hostname=hostname),
            )
        resolved = self._parse_ssh_g_output(resolve_result.stdout)
        probe = self._run_ssh(
            [
                "-T",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=5",
                target,
            ]
        )
        # OpenSSH often returns 1 for GitHub success banner; treat only hard failures as warnings.
        probe_ok = probe.returncode in {0, 1} and "permission denied" not in (probe.stderr or "").lower()
        if not probe_ok:
            self.logger.warning("ssh BatchMode probe for %s did not succeed; continuing after operator confirm", target)
        return {
            "target": target,
            "resolved": resolved,
            "batch_mode_probe_ok": probe_ok,
            "batch_mode_probe_returncode": probe.returncode,
        }

    def _build_gh_login_args(self, *, web: bool, scopes: Optional[str], hostname: Optional[str] = None, git_protocol: Optional[str] = None) -> list[str]:
        login_args = ["auth", "login"]
        if hostname and git_protocol:
            selected_scopes = (scopes or self.DEFAULT_GH_SCOPES).strip()
            login_args.extend(
                [
                    "--hostname",
                    hostname,
                    "--git-protocol",
                    git_protocol,
                    "--web",
                    "--scopes",
                    selected_scopes,
                ]
            )
            if git_protocol == "ssh":
                # OpenSSH config already owns keys (ssh -G). Do not ask to upload/select keys.
                login_args.append("--skip-ssh-key")
            return login_args
        if not web:
            return login_args
        selected_scopes = (scopes or self.DEFAULT_GH_SCOPES).strip()
        login_args.extend(
            [
                "--hostname",
                self.DEFAULT_HOSTNAME,
                "--git-protocol",
                "https",
                "--web",
                "--scopes",
                selected_scopes,
            ]
        )
        return login_args

    def _import_token_from_existing_gh_session(self, config_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Reuse an already-authenticated gh session instead of running auth login again."""
        self._require_gh_binary()
        token_result = self._run_gh(["auth", "token"], capture_output=True)
        if token_result.returncode != 0 or not token_result.stdout.strip():
            self.logger.info("no usable existing gh session token; interactive login required")
            return None
        store_result = self._store_token(token_result.stdout, config_path=config_path)
        self.logger.info("imported GitHub token from existing gh session into HAPE config")
        return {
            "method": "gh-session",
            "interactive": False,
            "config_path": store_result["config_path"],
            "token_stored": True,
        }

    def _complete_gh_login(self, login_args: list[str], config_path: Optional[str]) -> Dict[str, Any]:
        self.logger.info("starting GitHub CLI login for HAPE token bootstrap")
        login_result = self._run_gh(login_args, capture_output=False)
        if login_result.returncode != 0:
            raise HapeOperationError(
                code="GITHUB_AUTH_GH_LOGIN_FAILED",
                message=get_github_error_message("GITHUB_AUTH_GH_LOGIN_FAILED"),
            )
        token_result = self._run_gh(["auth", "token"], capture_output=True)
        if token_result.returncode != 0 or not token_result.stdout.strip():
            raise HapeOperationError(
                code="GITHUB_AUTH_GH_TOKEN_FAILED",
                message=get_github_error_message("GITHUB_AUTH_GH_TOKEN_FAILED"),
            )
        store_result = self._store_token(token_result.stdout, config_path=config_path)
        return {
            "method": "gh",
            "interactive": "--web" not in login_args,
            "config_path": store_result["config_path"],
            "token_stored": True,
        }

    def _print_bootstrap_plan(self, plan: Dict[str, Any]) -> None:
        print("Bootstrap plan (no secrets):")
        print(json.dumps(plan, indent=2, sort_keys=True))

    def login_with_gh(
        self,
        config_path: Optional[str] = None,
        web: bool = False,
        scopes: Optional[str] = None,
        non_interactive: bool = False,
        hostname: Optional[str] = None,
        git_protocol: Optional[str] = None,
    ) -> Dict[str, Any]:
        use_fixed = bool(hostname and git_protocol)
        if non_interactive and not web and not use_fixed:
            raise HapeValidationError(
                code="GITHUB_AUTH_NON_INTERACTIVE_REQUIRES_WEB",
                message=get_github_error_message("GITHUB_AUTH_NON_INTERACTIVE_REQUIRES_WEB"),
            )
        if use_fixed:
            selected_protocol = self._normalize_git_protocol(git_protocol or "")
            login_args = self._build_gh_login_args(
                web=True,
                scopes=scopes,
                hostname=hostname,
                git_protocol=selected_protocol,
            )
            result = self._complete_gh_login(login_args, config_path=config_path)
            result["scopes"] = (scopes or self.DEFAULT_GH_SCOPES).strip()
            result["hostname"] = hostname
            result["git_protocol"] = selected_protocol
            result["interactive"] = False
            return result

        use_web = web or non_interactive
        if not use_web and not sys.stdin.isatty():
            raise HapeValidationError(
                code="GITHUB_AUTH_NON_TTY",
                message=get_github_error_message("GITHUB_AUTH_NON_TTY"),
            )
        login_args = self._build_gh_login_args(web=use_web, scopes=scopes)
        result = self._complete_gh_login(login_args, config_path=config_path)
        if use_web:
            result["scopes"] = (scopes or self.DEFAULT_GH_SCOPES).strip()
            result["interactive"] = False
        else:
            result["scopes"] = None
        return result

    def login_with_token(self, token: str, config_path: Optional[str] = None) -> Dict[str, Any]:
        self.logger.info("storing GitHub token from stdin for HAPE config")
        store_result = self._store_token(token, config_path=config_path)
        return {
            "method": "token-stdin",
            "config_path": store_result["config_path"],
            "token_stored": True,
        }

    def configure_owner(self, owner: str, config_path: Optional[str] = None) -> Dict[str, Any]:
        normalized_owner = (owner or "").strip()
        if not normalized_owner:
            raise HapeValidationError(
                code="GITHUB_AUTH_OWNER_REQUIRED",
                message=get_github_error_message("GITHUB_AUTH_OWNER_REQUIRED"),
            )
        store_result = self.config_service.set_config_value(
            key=self.GITHUB_DEFAULT_OWNER_KEY,
            value=normalized_owner,
            config_path=config_path,
        )
        return {
            "config_path": store_result["config_path"],
            "owner": normalized_owner,
            "updated": True,
        }

    def status(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        resolved_path = config_path or Config.get_config_path()
        if config_path:
            Config.set_config_path(config_path)
        default_owner = Config.get_github_default_owner() or None
        Config.ensure_env_loaded()
        env_token = os.getenv(self.GITHUB_TOKEN_KEY)
        file_token: Optional[str] = None
        if os.path.exists(resolved_path):
            try:
                with open(resolved_path, "r", encoding="utf-8") as config_file:
                    file_token = (json.load(config_file).get(self.GITHUB_TOKEN_KEY) or None)
                    if file_token is not None:
                        file_token = str(file_token).strip() or None
            except (OSError, json.JSONDecodeError, TypeError):
                file_token = None
        if env_token not in (None, ""):
            token_source = "env"
        elif file_token:
            token_source = "config"
        else:
            token_source = None
        payload: Dict[str, Any] = {
            "config_path": resolved_path,
            "gh_available": shutil.which("gh") is not None,
            "token_configured": self._token_configured(),
            "token_source": token_source,
            "token_env_overrides_config": bool(
                env_token not in (None, "")
                and file_token
                and env_token.strip() != file_token
            ),
            "default_owner": default_owner,
            "authenticated_user": None,
            "auth_ok": False,
        }
        if not payload["token_configured"]:
            return payload
        try:
            user_info = self._get_github_service().get_authenticated_user_info()
            payload["authenticated_user"] = {
                "login": user_info.get("login"),
                "name": user_info.get("name"),
                "html_url": user_info.get("html_url"),
            }
            payload["auth_ok"] = True
        except Exception as exc:  # noqa: BLE001 - status must stay non-fatal
            self.logger.warning("github auth status probe failed: %s", exc)
            payload["auth_ok"] = False
        return payload

    def bootstrap(
        self,
        owner: Optional[str] = None,
        yes: bool = False,
        list_repos: bool = True,
        config_path: Optional[str] = None,
        token_stdin: Optional[str] = None,
        set_github_auth_method: bool = False,
        git_protocol: Optional[str] = None,
        hostname: Optional[str] = None,
    ) -> Dict[str, Any]:
        print("HAPE GitHub auth bootstrap")
        print("Tokens are stored in config.json and are never printed.")
        selected_owner = (owner or "").strip()
        if not selected_owner:
            raise HapeValidationError(
                code="GITHUB_AUTH_OWNER_REQUIRED",
                message=get_github_error_message("GITHUB_AUTH_OWNER_REQUIRED"),
            )
        selected_hostname = (hostname or self.DEFAULT_HOSTNAME).strip()
        selected_protocol = self._resolve_git_protocol(git_protocol, set_github_auth_method)

        self._require_gh_binary()
        ssh_preflight: Optional[Dict[str, Any]] = None
        if selected_protocol == "ssh":
            ssh_preflight = self._preflight_ssh_config(selected_hostname)

        login_method = "token-stdin" if token_stdin is not None else "gh-session-or-login"
        plan = {
            "hostname": selected_hostname,
            "git_protocol": selected_protocol,
            "owner": selected_owner,
            "login_method": login_method,
            "private_default": True,
            "actions": [
                "reuse existing gh session token when available, otherwise authenticate with GitHub CLI or token stdin",
                "store HAPE_GITHUB_TOKEN in config.json",
                "store HAPE_GITHUB_DEFAULT_OWNER in config.json",
                "verify auth status without printing the token",
            ],
            "ssh_preflight": ssh_preflight,
            "notes": [
                "SSH readiness uses OpenSSH config resolution (ssh -G); HAPE does not assume key paths.",
                "Bootstrap does not upload SSH keys when protocol is ssh (--skip-ssh-key).",
                "Bootstrap does not run init-repo.",
            ],
        }
        self._print_bootstrap_plan(plan)

        if not yes:
            approved = self._prompt_yes_no("Proceed with GitHub auth bootstrap?", default_yes=False)
            if not approved:
                raise HapeValidationError(
                    code="GITHUB_AUTH_BOOTSTRAP_CANCELLED",
                    message=get_github_error_message("GITHUB_AUTH_BOOTSTRAP_CANCELLED"),
                )

        if token_stdin is not None:
            login_result = self.login_with_token(token=token_stdin, config_path=config_path)
        else:
            login_result = self._import_token_from_existing_gh_session(config_path=config_path)
            if login_result is None:
                login_result = self.login_with_gh(
                    config_path=config_path,
                    hostname=selected_hostname,
                    git_protocol=selected_protocol,
                    scopes=self.DEFAULT_GH_SCOPES,
                )

        configure_result = self.configure_owner(owner=selected_owner, config_path=config_path)
        stored_config = self.config_service.show_config_file(config_path=config_path, reveal_secrets=False)
        stored_owner = stored_config.get("config", {}).get(self.GITHUB_DEFAULT_OWNER_KEY)
        if stored_owner != selected_owner:
            raise HapeOperationError(
                code="GITHUB_AUTH_VERIFY_FAILED",
                message=get_github_error_message("GITHUB_AUTH_VERIFY_FAILED"),
            )
        status_result = self.status(config_path=config_path)
        if not status_result.get("auth_ok"):
            raise HapeOperationError(
                code="GITHUB_AUTH_VERIFY_FAILED",
                message=get_github_error_message("GITHUB_AUTH_VERIFY_FAILED"),
            )

        repositories: list[Dict[str, Any]] = []
        if list_repos:
            try:
                repositories = self._get_github_service().list_repositories(org=selected_owner)
            except Exception as exc:  # noqa: BLE001 - list-repos is best-effort after verify
                self.logger.warning("bootstrap list-repos failed: %s", exc)

        print("Next: run Phase 1 init-repo commands from the operator runbook when ready.")
        return {
            "owner": selected_owner,
            "hostname": selected_hostname,
            "git_protocol": selected_protocol,
            "private_default": True,
            "plan": plan,
            "login": {
                "method": login_result.get("method"),
                "token_stored": login_result.get("token_stored"),
                "interactive": login_result.get("interactive"),
            },
            "configure": configure_result,
            "status": status_result,
            "user_info": status_result.get("authenticated_user"),
            "repository_count": len(repositories),
            "next_step": "phase-1-init-repo",
        }


if __name__ == "__main__":
    github_auth_service = GitHubAuthService()
    print(
        {
            "default_scopes": GitHubAuthService.DEFAULT_GH_SCOPES,
            "default_owner": GitHubAuthService.DEFAULT_OWNER,
            "default_hostname": GitHubAuthService.DEFAULT_HOSTNAME,
            "default_git_protocol": GitHubAuthService.DEFAULT_GIT_PROTOCOL,
            "token_key": GitHubAuthService.GITHUB_TOKEN_KEY,
            "owner_key": GitHubAuthService.GITHUB_DEFAULT_OWNER_KEY,
            "gh_available": shutil.which("gh") is not None,
            "ssh_available": shutil.which("ssh") is not None,
        }
    )
