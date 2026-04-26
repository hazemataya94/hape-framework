from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from threading import Lock
import time
from typing import Any

import jwt
import requests

from core.config import Config
from core.logging import LocalLogging


class GitHubClient:
    DEFAULT_TIMEOUT_SECONDS = 30
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_BACKOFF_SECONDS = 1.0
    DEFAULT_CACHE_TTL_SECONDS = 3600
    DEFAULT_APP_JWT_LIFETIME_MINUTES = 9
    DEFAULT_APP_TOKEN_REFRESH_SKEW_SECONDS = 60

    def __init__(self, base_url: str | None = None, token: str | None = None) -> None:
        self.logger = LocalLogging.get_logger("hape.git_hub_client")
        self.base_url = (base_url or Config.get_dora_github_api_url()).rstrip("/")
        self.auth_mode = "token"
        self.token = token or Config.get_dora_github_token()
        self.github_app_id: int | None = None
        self.github_installation_id: int | None = None
        self.github_app_private_key_path: str | None = None
        self._installation_token_expires_at = datetime.fromtimestamp(0, tz=timezone.utc)
        if not self.token and Config.has_dora_github_app_auth_config():
            self.auth_mode = "app"
            self.github_app_id = Config.get_dora_github_app_id()
            self.github_installation_id = Config.get_dora_github_installation_id()
            self.github_app_private_key_path = Config.get_dora_github_app_private_key_path()
        self.timeout_seconds = self.DEFAULT_TIMEOUT_SECONDS
        self.max_retries = self.DEFAULT_MAX_RETRIES
        self.retry_backoff_seconds = self.DEFAULT_RETRY_BACKOFF_SECONDS
        self.cache_ttl_seconds = self.DEFAULT_CACHE_TTL_SECONDS
        self._cache_lock = Lock()
        self._response_cache: dict[str, tuple[float, Any]] = {}
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"

    @staticmethod
    def _is_retryable_status_code(status_code: int) -> bool:
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

    def _build_github_app_jwt(self) -> str:
        if self.github_app_id is None or self.github_app_private_key_path is None:
            raise RuntimeError("GitHub App configuration is incomplete.")
        private_key = Path(self.github_app_private_key_path).expanduser().read_text(encoding="utf-8")
        now = datetime.now(tz=timezone.utc)
        payload = {
            "iat": int((now - timedelta(seconds=60)).timestamp()),
            "exp": int((now + timedelta(minutes=self.DEFAULT_APP_JWT_LIFETIME_MINUTES)).timestamp()),
            "iss": str(self.github_app_id),
        }
        encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256")
        if isinstance(encoded_jwt, bytes):
            return encoded_jwt.decode("utf-8")
        return encoded_jwt

    def _refresh_installation_token_if_needed(self) -> None:
        if self.auth_mode != "app":
            return
        if self.github_installation_id is None:
            raise RuntimeError("HAPE_GITHUB_INSTALLATION_ID is required for GitHub App authentication.")
        now = datetime.now(tz=timezone.utc)
        if self.token and now < (self._installation_token_expires_at - timedelta(seconds=self.DEFAULT_APP_TOKEN_REFRESH_SKEW_SECONDS)):
            return
        app_jwt = self._build_github_app_jwt()
        response = requests.post(
            url=f"{self.base_url}/app/installations/{self.github_installation_id}/access_tokens",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {app_jwt}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        token = payload.get("token")
        expires_at = payload.get("expires_at")
        if not isinstance(token, str) or not token:
            raise RuntimeError("GitHub App installation token response did not include a valid token.")
        if not isinstance(expires_at, str) or not expires_at:
            raise RuntimeError("GitHub App installation token response did not include expires_at.")
        self.token = token
        self._installation_token_expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        self.session.headers["Authorization"] = f"Bearer {self.token}"

    @staticmethod
    def _build_cache_key(endpoint_path: str, params: dict[str, Any] | None) -> str:
        params_payload = json.dumps(params or {}, sort_keys=True, separators=(",", ":"))
        return f"{endpoint_path}?{params_payload}"

    def _get_cached_response(self, cache_key: str) -> Any | None:
        now = time.time()
        with self._cache_lock:
            cached_entry = self._response_cache.get(cache_key)
            if cached_entry is None:
                return None
            cached_at_epoch_seconds, cached_payload = cached_entry
            if (now - cached_at_epoch_seconds) > self.cache_ttl_seconds:
                del self._response_cache[cache_key]
                return None
            return copy.deepcopy(cached_payload)

    def _set_cached_response(self, cache_key: str, payload: Any) -> None:
        with self._cache_lock:
            self._response_cache[cache_key] = (time.time(), copy.deepcopy(payload))

    def _request_json_get(self, endpoint_path: str, params: dict[str, Any] | None = None) -> Any:
        cache_key = self._build_cache_key(endpoint_path=endpoint_path, params=params)
        cached_response = self._get_cached_response(cache_key=cache_key)
        if cached_response is not None:
            return cached_response
        self._refresh_installation_token_if_needed()
        for retry_attempt in range(0, self.max_retries + 1):
            response: requests.Response | None = None
            try:
                response = self.session.get(
                    f"{self.base_url}{endpoint_path}",
                    params=params,
                    timeout=self.timeout_seconds,
                )
            except requests.RequestException as exc:
                if retry_attempt >= self.max_retries:
                    raise
                delay_seconds = self._compute_retry_delay_seconds(response=None, retry_attempt=retry_attempt + 1)
                self.logger.warning(
                    "GitHub request failed with transport error; retrying in %.2fs (attempt %s/%s): endpoint=%s error=%s",
                    delay_seconds,
                    retry_attempt + 1,
                    self.max_retries,
                    endpoint_path,
                    exc,
                )
                time.sleep(delay_seconds)
                continue

            if response.status_code == 401 and self.auth_mode == "app":
                if retry_attempt >= self.max_retries:
                    response.raise_for_status()
                self.token = ""
                self._refresh_installation_token_if_needed()
                continue

            if self._is_retryable_status_code(response.status_code):
                if retry_attempt >= self.max_retries:
                    response.raise_for_status()
                delay_seconds = self._compute_retry_delay_seconds(response=response, retry_attempt=retry_attempt + 1)
                self.logger.warning(
                    "GitHub request returned retryable status %s; retrying in %.2fs (attempt %s/%s): endpoint=%s",
                    response.status_code,
                    delay_seconds,
                    retry_attempt + 1,
                    self.max_retries,
                    endpoint_path,
                )
                time.sleep(delay_seconds)
                continue

            response.raise_for_status()
            payload = response.json()
            self._set_cached_response(cache_key=cache_key, payload=payload)
            return payload

        raise RuntimeError(f"GitHub request exhausted retries unexpectedly for endpoint '{endpoint_path}'.")

    def _request_json_post(self, endpoint_path: str, payload: dict[str, Any]) -> Any:
        self._refresh_installation_token_if_needed()
        for retry_attempt in range(0, self.max_retries + 1):
            response: requests.Response | None = None
            try:
                response = self.session.post(
                    f"{self.base_url}{endpoint_path}",
                    json=payload,
                    timeout=self.timeout_seconds,
                )
            except requests.RequestException as exc:
                if retry_attempt >= self.max_retries:
                    raise
                delay_seconds = self._compute_retry_delay_seconds(response=None, retry_attempt=retry_attempt + 1)
                self.logger.warning(
                    "GitHub request failed with transport error; retrying in %.2fs (attempt %s/%s): endpoint=%s error=%s",
                    delay_seconds,
                    retry_attempt + 1,
                    self.max_retries,
                    endpoint_path,
                    exc,
                )
                time.sleep(delay_seconds)
                continue

            if response.status_code == 401 and self.auth_mode == "app":
                if retry_attempt >= self.max_retries:
                    response.raise_for_status()
                self.token = ""
                self._refresh_installation_token_if_needed()
                continue

            if self._is_retryable_status_code(response.status_code):
                if retry_attempt >= self.max_retries:
                    response.raise_for_status()
                delay_seconds = self._compute_retry_delay_seconds(response=response, retry_attempt=retry_attempt + 1)
                self.logger.warning(
                    "GitHub request returned retryable status %s; retrying in %.2fs (attempt %s/%s): endpoint=%s",
                    response.status_code,
                    delay_seconds,
                    retry_attempt + 1,
                    self.max_retries,
                    endpoint_path,
                )
                time.sleep(delay_seconds)
                continue

            response.raise_for_status()
            return response.json()

        raise RuntimeError(f"GitHub POST request exhausted retries unexpectedly for endpoint '{endpoint_path}'.")

    def _request_json_put(self, endpoint_path: str, payload: dict[str, Any]) -> requests.Response:
        self._refresh_installation_token_if_needed()
        response = self.session.put(
            f"{self.base_url}{endpoint_path}",
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response

    def _collect_paginated(self, endpoint_path: str, base_params: dict[str, Any] | None = None, root_key: str | None = None) -> list[dict[str, Any]]:
        params = dict(base_params or {})
        params.setdefault("per_page", 100)
        page = 1
        items: list[dict[str, Any]] = []
        while True:
            params["page"] = page
            response_payload = self._request_json_get(endpoint_path=endpoint_path, params=params)
            page_items = response_payload.get(root_key, []) if root_key else response_payload
            if not isinstance(page_items, list) or not page_items:
                break
            items.extend(page_items)
            page += 1
        return items

    def get_org_repositories(self, org_name: str, include_archived: bool = False) -> list[dict[str, Any]]:
        self.logger.debug("get_org_repositories(org_name: %s, include_archived: %s)", org_name, include_archived)
        repositories = self._collect_paginated(endpoint_path=f"/orgs/{org_name}/repos", base_params={"type": "all"}, root_key=None)
        if include_archived:
            return repositories
        return [repo for repo in repositories if not bool(repo.get("archived", False))]

    def get_authenticated_user(self) -> dict[str, Any]:
        payload = self._request_json_get(endpoint_path="/user")
        if not isinstance(payload, dict):
            raise RuntimeError("Unexpected GitHub authenticated user response.")
        return payload

    def get_authenticated_organizations(self) -> list[dict[str, Any]]:
        payload = self._request_json_get(endpoint_path="/user/orgs")
        if not isinstance(payload, list):
            raise RuntimeError("Unexpected GitHub authenticated organizations response.")
        return payload

    def resolve_token_default_owner(self) -> str:
        try:
            user_payload = self.get_authenticated_user()
        except Exception:
            user_payload = {}
        user_login = str(user_payload.get("login", "")).strip()
        if user_login:
            return user_login
        try:
            organizations = self.get_authenticated_organizations()
        except Exception:
            organizations = []
        candidate_orgs = sorted(
            {
                str(organization.get("login", "")).strip()
                for organization in organizations
                if str(organization.get("login", "")).strip()
            }
        )
        if candidate_orgs:
            return candidate_orgs[0]
        return ""

    def create_repository(self, owner: str, repo_name: str, private: bool = True) -> dict[str, Any]:
        owner = owner.strip()
        repo_name = repo_name.strip()
        payload = {
            "name": repo_name,
            "private": private,
            "auto_init": False,
        }
        authenticated_owner = self.resolve_token_default_owner()
        if owner.lower() == authenticated_owner.lower():
            response_payload = self._request_json_post(endpoint_path="/user/repos", payload=payload)
        else:
            response_payload = self._request_json_post(endpoint_path=f"/orgs/{owner}/repos", payload=payload)
        if not isinstance(response_payload, dict):
            raise RuntimeError(f"Unexpected GitHub create repository response for owner={owner}, repo={repo_name}.")
        return response_payload

    def resolve_user_login_by_email(self, email: str) -> str:
        normalized_email = email.strip().lower()
        if not normalized_email:
            return ""
        payload = self._request_json_get(
            endpoint_path="/search/users",
            params={"q": f"{normalized_email} in:email", "per_page": 1},
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

    def add_repository_collaborator(self, owner: str, repo_name: str, username: str, permission: str = "push") -> bool:
        normalized_owner = owner.strip()
        normalized_repo_name = repo_name.strip()
        normalized_username = username.strip()
        normalized_permission = permission.strip().lower()
        if not normalized_owner or not normalized_repo_name or not normalized_username:
            return False
        response = self._request_json_put(
            endpoint_path=f"/repos/{normalized_owner}/{normalized_repo_name}/collaborators/{normalized_username}",
            payload={"permission": normalized_permission},
        )
        return response.status_code in {201, 204}

    def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        self.logger.debug("get_repository(owner: %s, repo: %s)", owner, repo)
        payload = self._request_json_get(endpoint_path=f"/repos/{owner}/{repo}")
        if not isinstance(payload, dict):
            raise RuntimeError(f"Unexpected GitHub repository response for {owner}/{repo}.")
        return payload

    def get_repository_workflow_runs(self, owner: str, repo: str, created_after: str, created_before: str, branch: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        self.logger.debug(
            "get_repository_workflow_runs(owner: %s, repo: %s, created_after: %s, created_before: %s, branch: %s, status: %s)",
            owner,
            repo,
            created_after,
            created_before,
            branch,
            status,
        )
        created_query = f"{created_after}..{created_before}"
        params: dict[str, Any] = {"created": created_query}
        if branch:
            params["branch"] = branch
        if status:
            params["status"] = status
        return self._collect_paginated(endpoint_path=f"/repos/{owner}/{repo}/actions/runs", base_params=params, root_key="workflow_runs")

    def get_workflow_run_jobs(self, owner: str, repo: str, run_id: int) -> list[dict[str, Any]]:
        self.logger.debug("get_workflow_run_jobs(owner: %s, repo: %s, run_id: %s)", owner, repo, run_id)
        return self._collect_paginated(endpoint_path=f"/repos/{owner}/{repo}/actions/runs/{run_id}/jobs", base_params={}, root_key="jobs")

    def get_repository_commits(self, owner: str, repo: str, sha: str, since: str | None = None, until: str | None = None) -> list[dict[str, Any]]:
        self.logger.debug(
            "get_repository_commits(owner: %s, repo: %s, sha: %s, since: %s, until: %s)",
            owner,
            repo,
            sha,
            since,
            until,
        )
        params: dict[str, Any] = {"sha": sha}
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        return self._collect_paginated(endpoint_path=f"/repos/{owner}/{repo}/commits", base_params=params, root_key=None)

    @staticmethod
    def parse_iso_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))


if __name__ == "__main__":
    print(GitHubClient)
