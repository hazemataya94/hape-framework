from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import time
from typing import Any

import jwt
import requests

from core.config import Config
from core.logging import LocalLogging


@dataclass
class GitHubAppRegistration:
    registration_id: str
    app_id: str
    private_key_pem: str
    expected_permissions: dict[str, str]
    organization_allowlist: tuple[str, ...] = field(default_factory=tuple)
    slug: str = ""
    client_id: str = ""
    client_secret: str = ""


class GitHubAppClientError(Exception):
    def __init__(self, code: str, status_code: int | None = None) -> None:
        self.code = code
        self.status_code = status_code
        super().__init__(code)


class GitHubAppClient:
    DEFAULT_BASE_URL = "https://api.github.example.com"
    DEFAULT_TIMEOUT_SECONDS = 30
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_BACKOFF_SECONDS = 1.0
    DEFAULT_APP_JWT_LIFETIME_MINUTES = 9
    DEFAULT_API_VERSION = "2022-11-28"

    def __init__(
        self,
        base_url: str | None = None,
        session: requests.Session | None = None,
        oauth_base_url: str | None = None,
    ) -> None:
        self.logger = LocalLogging.get_logger("hape.git_hub_app_client")
        self.base_url = (base_url or Config.get_github_app_api_url() or self.DEFAULT_BASE_URL).rstrip("/")
        self.oauth_base_url = (oauth_base_url or Config.get_github_app_oauth_url() or "https://github.example.com").rstrip("/")
        self.timeout_seconds = self.DEFAULT_TIMEOUT_SECONDS
        self.max_retries = self.DEFAULT_MAX_RETRIES
        self.retry_backoff_seconds = self.DEFAULT_RETRY_BACKOFF_SECONDS
        self.session = session or requests.Session()
        self.request_log: list[dict[str, Any]] = []

    def _is_retryable_status_code(self, status_code: int) -> bool:
        return status_code == 429 or 500 <= status_code <= 599

    def _compute_retry_delay_seconds(self, response: requests.Response | None, retry_attempt: int) -> float:
        if response is not None:
            retry_after_header = response.headers.get("Retry-After", "").strip()
            if retry_after_header:
                try:
                    retry_after_seconds = float(retry_after_header)
                    if retry_after_seconds > 0:
                        return retry_after_seconds
                except ValueError:
                    pass
        return self.retry_backoff_seconds * (2 ** (retry_attempt - 1))

    def _record_request(self, method: str, url: str, header_names: list[str]) -> None:
        self.request_log.append(
            {
                "method": method,
                "url": url,
                "header_names": sorted(header_names),
                "has_authorization": "Authorization" in header_names,
            }
        )
        self.logger.info("github_app_http method=%s path=%s", method, url)

    def _build_app_jwt(self, app_id: str, private_key_pem: str) -> str:
        now = datetime.now(tz=timezone.utc)
        payload = {
            "iat": int((now - timedelta(seconds=60)).timestamp()),
            "exp": int((now + timedelta(minutes=self.DEFAULT_APP_JWT_LIFETIME_MINUTES)).timestamp()),
            "iss": str(app_id),
        }
        encoded_jwt = jwt.encode(payload, private_key_pem, algorithm="RS256")
        if isinstance(encoded_jwt, bytes):
            return encoded_jwt.decode("utf-8")
        return encoded_jwt

    def _request(self, method: str, path: str, token: str, *, json_body: dict[str, Any] | None = None, params: dict[str, Any] | None = None, raw: bool = False) -> Any:
        if "://" in path or "?" in path.split("/", 1)[0]:
            raise GitHubAppClientError("invalid_path")
        url = f"{self.base_url}{path}"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": self.DEFAULT_API_VERSION,
        }
        self._record_request(method=method, url=url, header_names=list(headers.keys()))
        last_error: Exception | None = None
        for retry_attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_body,
                    params=params,
                    timeout=self.timeout_seconds,
                )
            except requests.RequestException as exc:
                last_error = exc
                if retry_attempt >= self.max_retries:
                    raise GitHubAppClientError("provider_unavailable") from exc
                time.sleep(min(self._compute_retry_delay_seconds(None, retry_attempt), 30))
                continue
            if response.status_code == 429:
                last_error = GitHubAppClientError("rate_limited", status_code=429)
                if retry_attempt >= self.max_retries:
                    raise last_error
                time.sleep(min(self._compute_retry_delay_seconds(response, retry_attempt), 30))
                continue
            if self._is_retryable_status_code(response.status_code):
                last_error = GitHubAppClientError("provider_unavailable", status_code=response.status_code)
                if retry_attempt >= self.max_retries:
                    raise last_error
                time.sleep(min(self._compute_retry_delay_seconds(response, retry_attempt), 30))
                continue
            if response.status_code == 404:
                raise GitHubAppClientError("not_found", status_code=404)
            if response.status_code == 409:
                raise GitHubAppClientError("conflict", status_code=409)
            if response.status_code == 422:
                raise GitHubAppClientError("unprocessable", status_code=422)
            if response.status_code >= 400:
                raise GitHubAppClientError("provider_unavailable", status_code=response.status_code)
            if raw:
                return response.content
            if response.status_code == 204:
                return {}
            payload = response.json()
            return payload
        if last_error is not None:
            raise last_error
        raise GitHubAppClientError("provider_unavailable")

    def mint_installation_token(self, registration: GitHubAppRegistration, installation_id: int) -> dict[str, Any]:
        app_jwt = self._build_app_jwt(registration.app_id, registration.private_key_pem)
        payload = self._request("POST", f"/app/installations/{installation_id}/access_tokens", app_jwt)
        token = payload.get("token")
        permissions = payload.get("permissions") or {}
        if not isinstance(token, str) or not token:
            raise GitHubAppClientError("provider_unavailable")
        if not isinstance(permissions, dict):
            raise GitHubAppClientError("provider_unavailable")
        return {
            "token": token,
            "permissions": {str(key): str(value) for key, value in permissions.items()},
            "expires_at": payload.get("expires_at"),
            "repository_selection": payload.get("repository_selection"),
        }

    def get_app_installation(self, registration: GitHubAppRegistration, installation_id: int) -> dict[str, Any]:
        app_jwt = self._build_app_jwt(registration.app_id, registration.private_key_pem)
        return self.get_installation(app_jwt, installation_id)

    def get_installation(self, token: str, installation_id: int) -> dict[str, Any]:
        payload = self._request("GET", f"/app/installations/{installation_id}", token)
        if not isinstance(payload, dict):
            raise GitHubAppClientError("provider_unavailable")
        return payload

    def exchange_user_code(
        self,
        registration: GitHubAppRegistration,
        authorization_code: str,
        callback_url: str,
        code_verifier: str,
    ) -> dict[str, str]:
        if not registration.client_id or not registration.client_secret:
            raise GitHubAppClientError("provider_unavailable")
        url = f"{self.oauth_base_url}/login/oauth/access_token"
        self._record_request("POST", url, ["Accept"])
        try:
            response = self.session.request(
                "POST",
                url,
                headers={"Accept": "application/json"},
                data={
                    "client_id": registration.client_id,
                    "client_secret": registration.client_secret,
                    "code": authorization_code,
                    "redirect_uri": callback_url,
                    "code_verifier": code_verifier,
                },
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise GitHubAppClientError("provider_unavailable") from exc
        if response.status_code >= 400:
            raise GitHubAppClientError("provider_unavailable", status_code=response.status_code)
        try:
            payload = response.json()
        except ValueError as exc:
            raise GitHubAppClientError("provider_unavailable") from exc
        if not isinstance(payload, dict):
            raise GitHubAppClientError("provider_unavailable")
        access_token = str(payload.get("access_token") or "").strip()
        if not access_token:
            raise GitHubAppClientError("provider_unavailable")
        return {
            "access_token": access_token,
            "refresh_token": str(payload.get("refresh_token") or "").strip(),
        }

    def get_authenticated_user(self, token: str) -> dict[str, Any]:
        payload = self._request("GET", "/user", token)
        if not isinstance(payload, dict):
            raise GitHubAppClientError("provider_unavailable")
        return payload

    def list_user_installations(self, token: str, page: int = 1, per_page: int = 100) -> dict[str, Any]:
        payload = self._request("GET", "/user/installations", token, params={"page": page, "per_page": per_page})
        if not isinstance(payload, dict):
            raise GitHubAppClientError("provider_unavailable")
        return payload

    def list_installation_repositories(self, token: str, page: int = 1, per_page: int = 30) -> dict[str, Any]:
        payload = self._request("GET", "/installation/repositories", token, params={"page": page, "per_page": per_page})
        if not isinstance(payload, dict):
            raise GitHubAppClientError("provider_unavailable")
        return payload

    def get_repository(self, token: str, owner: str, name: str) -> dict[str, Any]:
        payload = self._request("GET", f"/repos/{owner}/{name}", token)
        if not isinstance(payload, dict):
            raise GitHubAppClientError("provider_unavailable")
        return payload

    def get_commit(self, token: str, owner: str, repo: str, ref: str) -> dict[str, Any]:
        payload = self._request("GET", f"/repos/{owner}/{repo}/commits/{ref}", token)
        if not isinstance(payload, dict):
            raise GitHubAppClientError("provider_unavailable")
        return payload

    def get_git_ref(self, token: str, owner: str, repo: str, ref: str) -> dict[str, Any]:
        payload = self._request("GET", f"/repos/{owner}/{repo}/git/ref/{ref}", token)
        if not isinstance(payload, dict):
            raise GitHubAppClientError("provider_unavailable")
        return payload

    def get_git_tree(self, token: str, owner: str, repo: str, tree_sha: str, recursive: bool = False) -> dict[str, Any]:
        params = {"recursive": "1"} if recursive else None
        payload = self._request("GET", f"/repos/{owner}/{repo}/git/trees/{tree_sha}", token, params=params)
        if not isinstance(payload, dict):
            raise GitHubAppClientError("provider_unavailable")
        return payload

    def get_git_blob(self, token: str, owner: str, repo: str, blob_sha: str) -> dict[str, Any]:
        payload = self._request("GET", f"/repos/{owner}/{repo}/git/blobs/{blob_sha}", token)
        if not isinstance(payload, dict):
            raise GitHubAppClientError("provider_unavailable")
        return payload

    def create_organization_repository(self, token: str, org: str, name: str) -> dict[str, Any]:
        payload = self._request(
            "POST",
            f"/orgs/{org}/repos",
            token,
            json_body={"name": name, "private": True, "auto_init": False},
        )
        if not isinstance(payload, dict):
            raise GitHubAppClientError("provider_unavailable")
        return payload

    def resolve_user_login_by_email(self, token: str, email: str) -> str:
        normalized_email = email.strip().lower()
        if not normalized_email:
            return ""
        payload = self._request(
            "GET",
            "/search/users",
            token,
            params={"q": f"{normalized_email} in:email", "per_page": "1"},
        )
        if not isinstance(payload, dict):
            return ""
        users = payload.get("items")
        if not isinstance(users, list) or not users:
            return ""
        first_user = users[0]
        if not isinstance(first_user, dict):
            return ""
        return str(first_user.get("login", "")).strip()

    def add_repository_collaborator(
        self,
        token: str,
        owner: str,
        repo_name: str,
        username: str,
        permission: str = "push",
    ) -> bool:
        normalized_owner = owner.strip()
        normalized_repo_name = repo_name.strip()
        normalized_username = username.strip()
        if not normalized_owner or not normalized_repo_name or not normalized_username:
            return False
        self._request(
            "PUT",
            f"/repos/{normalized_owner}/{normalized_repo_name}/collaborators/{normalized_username}",
            token,
            json_body={"permission": permission.strip().lower() or "push"},
        )
        return True

    def create_git_blob(self, token: str, owner: str, repo: str, content_base64: str) -> dict[str, Any]:
        payload = self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/blobs",
            token,
            json_body={"content": content_base64, "encoding": "base64"},
        )
        if not isinstance(payload, dict):
            raise GitHubAppClientError("provider_unavailable")
        return payload

    def create_git_tree(self, token: str, owner: str, repo: str, tree: list[dict[str, str]]) -> dict[str, Any]:
        payload = self._request("POST", f"/repos/{owner}/{repo}/git/trees", token, json_body={"tree": tree})
        if not isinstance(payload, dict):
            raise GitHubAppClientError("provider_unavailable")
        return payload

    def create_git_commit(self, token: str, owner: str, repo: str, message: str, tree_sha: str, parents: list[str]) -> dict[str, Any]:
        payload = self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/commits",
            token,
            json_body={"message": message, "tree": tree_sha, "parents": parents},
        )
        if not isinstance(payload, dict):
            raise GitHubAppClientError("provider_unavailable")
        return payload

    def create_git_ref(self, token: str, owner: str, repo: str, ref: str, sha: str) -> dict[str, Any]:
        payload = self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/refs",
            token,
            json_body={"ref": ref, "sha": sha},
        )
        if not isinstance(payload, dict):
            raise GitHubAppClientError("provider_unavailable")
        return payload

    def update_git_ref(self, token: str, owner: str, repo: str, ref: str, sha: str) -> dict[str, Any]:
        payload = self._request(
            "PATCH",
            f"/repos/{owner}/{repo}/git/refs/{ref}",
            token,
            json_body={"sha": sha, "force": False},
        )
        if not isinstance(payload, dict):
            raise GitHubAppClientError("provider_unavailable")
        return payload

    def create_git_tag(self, token: str, owner: str, repo: str, tag: str, message: str, object_sha: str) -> dict[str, Any]:
        payload = self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/tags",
            token,
            json_body={"tag": tag, "message": message, "object": object_sha, "type": "commit"},
        )
        if not isinstance(payload, dict):
            raise GitHubAppClientError("provider_unavailable")
        return payload

    def delete_repository(self, token: str, owner: str, repo: str) -> None:
        self._request("DELETE", f"/repos/{owner}/{repo}", token)


if __name__ == "__main__":
    print(GitHubAppClient.DEFAULT_BASE_URL)
