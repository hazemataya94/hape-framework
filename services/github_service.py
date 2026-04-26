from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

import requests

from clients.github_client import GitHubClient
from core.config import Config
from core.errors.exceptions import HapeExternalError, HapeValidationError
from core.errors.messages.github_error_messages import get_github_error_message
from core.logging import LocalLogging


class GitHubService:
    @staticmethod
    def _extract_create_repo_failure_reason(exc: Exception) -> str:
        if isinstance(exc, requests.HTTPError) and exc.response is not None:
            response = exc.response
            reason_parts = [f"status={response.status_code}"]
            message = ""
            details = ""
            try:
                response_payload = response.json()
            except ValueError:
                response_payload = None
            if isinstance(response_payload, dict):
                message = str(response_payload.get("message", "")).strip()
                errors = response_payload.get("errors")
                if isinstance(errors, list):
                    detail_parts: list[str] = []
                    for error_item in errors[:3]:
                        if isinstance(error_item, dict):
                            error_segments = [
                                str(error_item.get("field", "")).strip(),
                                str(error_item.get("code", "")).strip(),
                                str(error_item.get("message", "")).strip(),
                            ]
                            error_text = " ".join(segment for segment in error_segments if segment)
                            if error_text:
                                detail_parts.append(error_text)
                        else:
                            error_text = str(error_item).strip()
                            if error_text:
                                detail_parts.append(error_text)
                    details = "; ".join(detail_parts)
            if message:
                reason_parts.append(message)
            if details:
                reason_parts.append(f"errors={details}")
            return " | ".join(reason_parts)
        return str(exc).strip() or "unknown GitHub API error"

    def _resolve_repo_path(self, repo_path: str) -> Path:
        resolved_repo_path = Path(repo_path).expanduser().resolve()
        if not resolved_repo_path.exists():
            raise HapeValidationError(
                code="GITHUB_REPO_PATH_NOT_FOUND",
                message=get_github_error_message(
                    "GITHUB_REPO_PATH_NOT_FOUND",
                    repo_path=str(resolved_repo_path),
                ),
            )
        if not resolved_repo_path.is_dir():
            raise HapeValidationError(
                code="GITHUB_REPO_PATH_NOT_DIRECTORY",
                message=get_github_error_message(
                    "GITHUB_REPO_PATH_NOT_DIRECTORY",
                    repo_path=str(resolved_repo_path),
                ),
            )
        if (resolved_repo_path / ".git").exists():
            raise HapeValidationError(
                code="GITHUB_REPO_ALREADY_INITIALIZED",
                message=get_github_error_message(
                    "GITHUB_REPO_ALREADY_INITIALIZED",
                    repo_path=str(resolved_repo_path),
                ),
            )
        return resolved_repo_path

    @staticmethod
    def _resolve_repo_name(repo_path: Path, name: str | None) -> str:
        if name and name.strip():
            return name.strip()
        return repo_path.name.strip()

    @staticmethod
    def _resolve_visibility(visibility: str) -> bool:
        normalized_visibility = visibility.strip().lower()
        if normalized_visibility not in {"private", "public"}:
            raise HapeValidationError(
                code="GITHUB_VISIBILITY_INVALID",
                message=get_github_error_message(
                    "GITHUB_VISIBILITY_INVALID",
                    visibility=visibility,
                ),
            )
        return normalized_visibility == "private"

    def _resolve_owner(self, owner: str | None) -> str:
        if owner and owner.strip():
            return owner.strip()
        configured_default_owner = Config.get_github_default_owner()
        if configured_default_owner:
            return configured_default_owner
        resolved_owner = self.github_client.resolve_token_default_owner()
        if not resolved_owner:
            raise HapeValidationError(
                code="GITHUB_OWNER_UNRESOLVED",
                message=get_github_error_message("GITHUB_OWNER_UNRESOLVED"),
            )
        return resolved_owner

    @staticmethod
    def _run_git_init(repo_path: Path) -> None:
        subprocess.run(
            ["git", "init"],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
            text=True,
        )

    @staticmethod
    def _run_git_add_remote(repo_path: Path, remote_url: str) -> None:
        subprocess.run(
            ["git", "remote", "add", "origin", remote_url],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
            text=True,
        )

    @staticmethod
    def _read_global_git_email() -> str:
        completed_process = subprocess.run(
            ["git", "config", "--global", "user.email"],
            check=True,
            capture_output=True,
            text=True,
        )
        return completed_process.stdout.strip()

    def _resolve_host_git_admin_login(self) -> str:
        try:
            global_git_email = self._read_global_git_email()
        except subprocess.CalledProcessError as exc:
            raise HapeValidationError(
                code="GITHUB_GLOBAL_GIT_EMAIL_UNAVAILABLE",
                message=get_github_error_message("GITHUB_GLOBAL_GIT_EMAIL_UNAVAILABLE"),
            ) from exc
        if not global_git_email:
            raise HapeValidationError(
                code="GITHUB_GLOBAL_GIT_EMAIL_UNAVAILABLE",
                message=get_github_error_message("GITHUB_GLOBAL_GIT_EMAIL_UNAVAILABLE"),
            )
        try:
            resolved_login = self.github_client.resolve_user_login_by_email(email=global_git_email)
        except Exception as exc:
            raise HapeExternalError(
                code="GITHUB_USER_LOOKUP_FAILED",
                message=get_github_error_message(
                    "GITHUB_USER_LOOKUP_FAILED",
                    email=global_git_email,
                ),
            ) from exc
        if not resolved_login:
            raise HapeValidationError(
                code="GITHUB_USER_LOGIN_UNRESOLVED",
                message=get_github_error_message(
                    "GITHUB_USER_LOGIN_UNRESOLVED",
                    email=global_git_email,
                ),
            )
        return resolved_login

    def _ensure_host_user_admin_access(self, owner: str, repo_name: str) -> str:
        admin_login = self._resolve_host_git_admin_login()
        try:
            collaborator_added = self.github_client.add_repository_collaborator(
                owner=owner,
                repo_name=repo_name,
                username=admin_login,
                permission="admin",
            )
        except Exception as exc:
            raise HapeExternalError(
                code="GITHUB_ADD_ADMIN_COLLABORATOR_FAILED",
                message=get_github_error_message(
                    "GITHUB_ADD_ADMIN_COLLABORATOR_FAILED",
                    owner=owner,
                    repo_name=repo_name,
                    username=admin_login,
                ),
            ) from exc
        if not collaborator_added:
            raise HapeExternalError(
                code="GITHUB_ADD_ADMIN_COLLABORATOR_FAILED",
                message=get_github_error_message(
                    "GITHUB_ADD_ADMIN_COLLABORATOR_FAILED",
                    owner=owner,
                    repo_name=repo_name,
                    username=admin_login,
                ),
            )
        return admin_login

    def __init__(self, github_client: GitHubClient | None = None) -> None:
        self.github_client = github_client or GitHubClient()
        self.logger = LocalLogging.get_logger("hape.git_hub_service")

    def init_repo(self, repo_path: str, owner: str | None = None, name: str | None = None, visibility: str = "private") -> dict[str, Any]:
        self.logger.debug(
            "init_repo(repo_path=%s, owner=%s, name=%s, visibility=%s)",
            repo_path,
            owner or "",
            name or "",
            visibility,
        )
        resolved_repo_path = self._resolve_repo_path(repo_path=repo_path)
        resolved_repo_name = self._resolve_repo_name(repo_path=resolved_repo_path, name=name)
        is_private_repo = self._resolve_visibility(visibility=visibility)
        resolved_owner = self._resolve_owner(owner=owner)
        try:
            repository_data = self.github_client.create_repository(
                owner=resolved_owner,
                repo_name=resolved_repo_name,
                private=is_private_repo,
            )
        except Exception as exc:
            reason = self._extract_create_repo_failure_reason(exc=exc)
            self.logger.error("create_repository failed for %s/%s: %s", resolved_owner, resolved_repo_name, reason)
            raise HapeExternalError(
                code="GITHUB_CREATE_REPO_FAILED",
                message=get_github_error_message(
                    "GITHUB_CREATE_REPO_FAILED_WITH_REASON",
                    owner=resolved_owner,
                    repo_name=resolved_repo_name,
                    reason=reason,
                ),
            ) from exc
        ssh_clone_url = str(repository_data.get("ssh_url", "")).strip()
        if not ssh_clone_url:
            raise HapeExternalError(
                code="GITHUB_CREATE_REPO_INVALID_RESPONSE",
                message=get_github_error_message(
                    "GITHUB_CREATE_REPO_INVALID_RESPONSE",
                    owner=resolved_owner,
                    repo_name=resolved_repo_name,
                ),
            )
        admin_login = self._ensure_host_user_admin_access(owner=resolved_owner, repo_name=resolved_repo_name)
        try:
            self._run_git_init(repo_path=resolved_repo_path)
            self._run_git_add_remote(repo_path=resolved_repo_path, remote_url=ssh_clone_url)
        except subprocess.CalledProcessError as exc:
            raise HapeExternalError(
                code="GITHUB_LOCAL_GIT_INIT_FAILED",
                message=get_github_error_message(
                    "GITHUB_LOCAL_GIT_INIT_FAILED",
                    repo_path=str(resolved_repo_path),
                ),
            ) from exc
        self.logger.info(
            "Repository initialized at %s and created as %s/%s with admin collaborator %s",
            resolved_repo_path,
            resolved_owner,
            resolved_repo_name,
            admin_login,
        )
        return {
            "full_name": str(repository_data.get("full_name", f"{resolved_owner}/{resolved_repo_name}")),
            "html_url": str(repository_data.get("html_url", "")),
            "clone_url": ssh_clone_url,
            "local_path": str(resolved_repo_path),
            "admin_login": admin_login,
        }


if __name__ == "__main__":
    print(GitHubService)
