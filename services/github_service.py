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
    DELETE_REPOS_CONFIRMATION_PHRASE = "delete selected repos"

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

    @staticmethod
    def _resolve_repository_target(org: str | None) -> tuple[str, str | None]:
        normalized_org = str(org or "").strip()
        if normalized_org:
            return "org", normalized_org
        return "user", None

    @staticmethod
    def _normalize_repo_filter_values(values: list[str] | None) -> list[str]:
        normalized_values: list[str] = []
        if not values:
            return normalized_values
        for raw_value in values:
            for token in str(raw_value).split(","):
                normalized_token = token.strip()
                if normalized_token:
                    normalized_values.append(normalized_token)
        return normalized_values

    @staticmethod
    def _repository_matches_filter(repository: dict[str, Any], filter_values: set[str]) -> bool:
        if not filter_values:
            return False
        repo_name = str(repository.get("name", "")).strip().lower()
        repo_full_name = str(repository.get("full_name", "")).strip().lower()
        return repo_name in filter_values or repo_full_name in filter_values

    @staticmethod
    def _resolve_delete_org(org: str) -> str:
        normalized_org = org.strip()
        if not normalized_org:
            raise HapeValidationError(
                code="GITHUB_DELETE_REPOS_ORG_REQUIRED",
                message=get_github_error_message("GITHUB_DELETE_REPOS_ORG_REQUIRED"),
            )
        return normalized_org

    @staticmethod
    def _normalize_repository_payload(repository: dict[str, Any]) -> dict[str, Any]:
        owner_payload = repository.get("owner", {})
        if not isinstance(owner_payload, dict):
            owner_payload = {}
        return {
            "id": int(repository.get("id", 0)),
            "name": str(repository.get("name", "")),
            "full_name": str(repository.get("full_name", "")),
            "owner_login": str(owner_payload.get("login", "")),
            "private": bool(repository.get("private", False)),
            "archived": bool(repository.get("archived", False)),
            "default_branch": str(repository.get("default_branch", "")),
            "html_url": str(repository.get("html_url", "")),
            "ssh_url": str(repository.get("ssh_url", "")),
        }

    @staticmethod
    def _normalize_authenticated_user_payload(user_payload: dict[str, Any]) -> dict[str, str]:
        return {
            "login": str(user_payload.get("login", "")),
            "name": str(user_payload.get("name", "")),
            "html_url": str(user_payload.get("html_url", "")),
        }

    @staticmethod
    def _normalize_delete_repository_payload(repository: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": str(repository.get("name", "")),
            "full_name": str(repository.get("full_name", "")),
            "private": bool(repository.get("private", False)),
            "archived": bool(repository.get("archived", False)),
            "html_url": str(repository.get("html_url", "")),
        }

    def __init__(self, github_client: GitHubClient | None = None) -> None:
        self.github_client = github_client or GitHubClient()
        self.logger = LocalLogging.get_logger("hape.git_hub_service")

    def list_repositories(self, org: str | None = None, include_archived: bool = False) -> list[dict[str, Any]]:
        self.logger.debug(
            "list_repositories(org=%s, include_archived=%s)",
            org or "",
            include_archived,
        )
        normalized_scope, normalized_org = self._resolve_repository_target(org=org)
        scope_target = normalized_org or "authenticated-user"
        try:
            if normalized_scope == "user":
                repositories = self.github_client.get_authenticated_user_repositories(include_archived=include_archived)
            else:
                repositories = self.github_client.get_org_repositories(org_name=normalized_org or "", include_archived=include_archived)
        except Exception as exc:
            raise HapeExternalError(
                code="GITHUB_LIST_REPOS_FAILED",
                message=get_github_error_message(
                    "GITHUB_LIST_REPOS_FAILED",
                    scope=normalized_scope,
                    scope_target=scope_target,
                ),
            ) from exc
        normalized_repositories = [self._normalize_repository_payload(repository=repository) for repository in repositories]
        normalized_repositories.sort(key=lambda item: str(item.get("full_name", "")))
        return normalized_repositories

    def get_authenticated_user_info(self) -> dict[str, str]:
        self.logger.debug("get_authenticated_user_info()")
        try:
            user_payload = self.github_client.get_authenticated_user()
        except Exception as exc:
            raise HapeExternalError(
                code="GITHUB_AUTHENTICATED_USER_INFO_FAILED",
                message=get_github_error_message("GITHUB_AUTHENTICATED_USER_INFO_FAILED"),
            ) from exc
        return self._normalize_authenticated_user_payload(user_payload=user_payload)

    def get_delete_repositories_confirmation_phrase(self) -> str:
        return self.DELETE_REPOS_CONFIRMATION_PHRASE

    def list_repositories_for_deletion(self, org: str, include: list[str] | None = None, exclude: list[str] | None = None, delete_all: bool = False) -> list[dict[str, Any]]:
        normalized_org = self._resolve_delete_org(org=org)
        include_values = self._normalize_repo_filter_values(values=include)
        exclude_values = {value.lower() for value in self._normalize_repo_filter_values(values=exclude)}
        if not delete_all and not include_values:
            raise HapeValidationError(
                code="GITHUB_DELETE_REPOS_SELECTION_REQUIRED",
                message=get_github_error_message("GITHUB_DELETE_REPOS_SELECTION_REQUIRED"),
            )
        try:
            repositories = self.github_client.get_org_repositories(org_name=normalized_org, include_archived=True)
        except Exception as exc:
            raise HapeExternalError(
                code="GITHUB_DELETE_REPOS_LIST_FAILED",
                message=get_github_error_message(
                    "GITHUB_DELETE_REPOS_LIST_FAILED",
                    org=normalized_org,
                ),
            ) from exc
        selected_repositories: list[dict[str, Any]]
        if delete_all:
            selected_repositories = repositories
        else:
            include_value_set = {value.lower() for value in include_values}
            selected_repositories = [repository for repository in repositories if self._repository_matches_filter(repository=repository, filter_values=include_value_set)]
            missing_include_values = sorted(
                value
                for value in include_values
                if value.lower() not in {
                    str(repository.get("name", "")).strip().lower()
                    for repository in repositories
                }
                and value.lower() not in {
                    str(repository.get("full_name", "")).strip().lower()
                    for repository in repositories
                }
            )
            if missing_include_values:
                raise HapeValidationError(
                    code="GITHUB_DELETE_REPOS_INCLUDE_NOT_FOUND",
                    message=get_github_error_message(
                        "GITHUB_DELETE_REPOS_INCLUDE_NOT_FOUND",
                        missing=", ".join(missing_include_values),
                    ),
                )
        if exclude_values:
            selected_repositories = [
                repository
                for repository in selected_repositories
                if not self._repository_matches_filter(repository=repository, filter_values=exclude_values)
            ]
        if not selected_repositories:
            raise HapeValidationError(
                code="GITHUB_DELETE_REPOS_EMPTY_AFTER_FILTERS",
                message=get_github_error_message("GITHUB_DELETE_REPOS_EMPTY_AFTER_FILTERS"),
            )
        normalized_selected_repositories = [
            self._normalize_delete_repository_payload(repository=repository)
            for repository in selected_repositories
        ]
        normalized_selected_repositories.sort(key=lambda item: str(item.get("full_name", "")))
        return normalized_selected_repositories

    def delete_repositories(self, org: str, include: list[str] | None = None, exclude: list[str] | None = None, delete_all: bool = False, confirmation_phrase: str = "") -> dict[str, Any]:
        expected_confirmation_phrase = self.get_delete_repositories_confirmation_phrase()
        if confirmation_phrase.strip() != expected_confirmation_phrase:
            raise HapeValidationError(
                code="GITHUB_DELETE_REPOS_CONFIRMATION_MISMATCH",
                message=get_github_error_message(
                    "GITHUB_DELETE_REPOS_CONFIRMATION_MISMATCH",
                    expected_phrase=expected_confirmation_phrase,
                ),
            )
        normalized_org = self._resolve_delete_org(org=org)
        repositories_for_deletion = self.list_repositories_for_deletion(
            org=normalized_org,
            include=include,
            exclude=exclude,
            delete_all=delete_all,
        )
        deleted_repositories: list[str] = []
        for repository in repositories_for_deletion:
            repo_name = str(repository.get("name", "")).strip()
            full_name = str(repository.get("full_name", "")).strip()
            if not repo_name:
                continue
            try:
                delete_succeeded = self.github_client.delete_repository(owner=normalized_org, repo_name=repo_name)
            except Exception as exc:
                raise HapeExternalError(
                    code="GITHUB_DELETE_REPO_FAILED",
                    message=get_github_error_message(
                        "GITHUB_DELETE_REPO_FAILED",
                        full_name=full_name or f"{normalized_org}/{repo_name}",
                    ),
                ) from exc
            if not delete_succeeded:
                raise HapeExternalError(
                    code="GITHUB_DELETE_REPO_FAILED",
                    message=get_github_error_message(
                        "GITHUB_DELETE_REPO_FAILED",
                        full_name=full_name or f"{normalized_org}/{repo_name}",
                    ),
                )
            deleted_repositories.append(full_name or f"{normalized_org}/{repo_name}")
        deleted_repositories.sort()
        return {
            "org": normalized_org,
            "deleted_repositories": deleted_repositories,
            "deleted_count": len(deleted_repositories),
        }

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
