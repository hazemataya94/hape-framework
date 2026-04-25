from __future__ import annotations

from typing import Any

import requests

from core.logging import LocalLogging
from utils.urls_utils import UrlsUtils


class GrafanaClient:
    DEFAULT_TIMEOUT_SECONDS = 30

    def __init__(self, base_url: str, token: str | None = None, username: str | None = None, password: str | None = None, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> None:
        self.logger = LocalLogging.get_logger("hape.grafana_client")
        self.base_url = UrlsUtils.normalize_grafana_base_url(base_url)
        self.timeout_seconds = timeout_seconds
        self.auth = self._build_auth(username=username, password=password)
        self.session = requests.Session()
        self.session.headers.update(self._build_headers(token=token))
        self.session.auth = self.auth

    @staticmethod
    def _build_headers(token: str | None) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @staticmethod
    def _build_auth(username: str | None, password: str | None) -> tuple[str, str] | None:
        if username is None and password is None:
            return None
        if username is None or password is None:
            raise ValueError("Both Grafana username and password are required for basic auth.")
        return username, password

    def _request_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        self.logger.debug(f"_request_json(path: {path}, params: {params})")
        response = self.session.get(url, params=params, timeout=self.timeout_seconds, auth=self.auth)
        response.raise_for_status()
        if not response.content:
            return None
        return response.json()

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        self.logger.debug(f"_request(method: {method}, path: {path}, payload: {payload}, params: {params})")
        response = self.session.request(
            method=method,
            url=url,
            json=payload,
            params=params,
            timeout=self.timeout_seconds,
            auth=self.auth,
        )
        response.raise_for_status()
        if not response.content:
            return None
        return response.json()

    def list_datasources(self) -> list[dict[str, Any]]:
        self.logger.debug("list_datasources()")
        data = self._request_json("/api/datasources")
        if isinstance(data, list):
            return data
        return []

    def list_dashboards(self) -> list[dict[str, Any]]:
        self.logger.debug("list_dashboards()")
        page = 1
        all_dashboards: list[dict[str, Any]] = []
        while True:
            data = self._request_json("/api/search", params={"type": "dash-db", "limit": 5000, "page": page})
            if not data:
                break
            if not isinstance(data, list):
                break
            all_dashboards.extend(data)
            page += 1
        return all_dashboards

    def create_user(self, login: str, email: str, password: str, name: str | None = None) -> dict[str, Any]:
        self.logger.debug(f"create_user(login: {login}, email: {email})")
        payload = {"name": name or login, "email": email, "login": login, "password": password}
        data = self._request("POST", "/api/admin/users", payload=payload)
        if isinstance(data, dict):
            return data
        return {}

    def create_service_account(self, name: str, role: str = "Viewer") -> dict[str, Any]:
        self.logger.debug(f"create_service_account(name: {name}, role: {role})")
        payload = {"name": name, "role": role}
        data = self._request("POST", "/api/serviceaccounts", payload=payload)
        if isinstance(data, dict):
            return data
        return {}

    def create_service_account_token(self, service_account_id: int, token_name: str) -> dict[str, Any]:
        self.logger.debug(f"create_service_account_token(service_account_id: {service_account_id}, token_name: {token_name})")
        payload = {"name": token_name}
        data = self._request("POST", f"/api/serviceaccounts/{service_account_id}/tokens", payload=payload)
        if isinstance(data, dict):
            return data
        return {}

    def ensure_dashboard_viewer_permission(self, dashboard_uid: str, user_id: int) -> dict[str, Any]:
        self.logger.debug(f"ensure_dashboard_viewer_permission(dashboard_uid: {dashboard_uid}, user_id: {user_id})")
        payload = {
            "items": [
                {"userId": user_id, "permission": 1},
            ]
        }
        data = self._request("POST", f"/api/dashboards/uid/{dashboard_uid}/permissions", payload=payload)
        if isinstance(data, dict):
            return data
        return {}

    def get_dashboard_by_uid(self, uid: str) -> dict[str, Any]:
        self.logger.debug(f"get_dashboard_by_uid(uid: {uid})")
        data = self._request_json(f"/api/dashboards/uid/{uid}")
        if isinstance(data, dict):
            return data
        return {}

    def find_dashboard_links(self, namespace: str | None, workload_name: str | None, node_name: str | None) -> dict[str, str]:
        self.logger.debug(
            f"find_dashboard_links(namespace: {namespace}, workload_name: {workload_name}, node_name: {node_name})"
        )
        dashboards = self.list_dashboards()
        match_tokens = [token.lower() for token in [namespace, workload_name, node_name] if token]
        links: dict[str, str] = {}
        for dashboard in dashboards:
            uid = dashboard.get("uid")
            title = str(dashboard.get("title", ""))
            url = dashboard.get("url")
            if not uid or not url:
                continue
            normalized_title = title.lower()
            if match_tokens and not any(token in normalized_title for token in match_tokens):
                continue
            links[title or str(uid)] = f"{self.base_url}{url}"
        return links

    def build_dashboard_url_for_resource(self, resource_kind: str, resource_name: str, namespace: str | None = None) -> str:
        self.logger.debug(
            f"build_dashboard_url_for_resource(resource_kind: {resource_kind}, resource_name: {resource_name}, namespace: {namespace})"
        )
        title_tokens = [resource_kind, resource_name]
        if namespace:
            title_tokens.append(namespace)
        normalized_tokens = [token.lower() for token in title_tokens if token]
        for dashboard in self.list_dashboards():
            dashboard_title = str(dashboard.get("title", "")).lower()
            dashboard_url = dashboard.get("url")
            if dashboard_url and all(token in dashboard_title for token in normalized_tokens):
                return f"{self.base_url}{dashboard_url}"
        return f"{self.base_url}/dashboards"

if __name__ == "__main__":
    
    grafana_client = GrafanaClient(
        base_url="http://127.0.0.1:51716",
        token="",
        username="user",
        password="password",
    )
    grafana_datasources = grafana_client.list_dashboards()
    print(len(grafana_datasources))
