import re
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Dict, List, Optional

import requests

from utils.datetime_utils import DatetimeUtils

from core.logging import LocalLogging
from core.config import Config


class GitLabClient:
    
    def __init__(self) -> None:
        self.logger = LocalLogging.get_logger("hape.gitlab_client")
        self.dry_run = True
        self.gitlab_token = Config.get_gitlab_token()
        gitlab_domain = Config.get_gitlab_domain()
        self.gitlab_url = f"https://{gitlab_domain}"

    def _build_headers(self) -> dict[str, str]:
        return {"Private-Token": self.gitlab_token}

    def _request_json_get(self, endpoint_path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.gitlab_url}{endpoint_path}"
        response = requests.get(url, headers=self._build_headers(), params=params)
        response.raise_for_status()
        return response.json()

    def _collect_paginated(self, endpoint_path: str, base_params: dict[str, Any]) -> list[dict[str, Any]]:
        page = 1
        items: list[dict[str, Any]] = []
        while True:
            params = {**base_params, "per_page": 100, "page": page}
            page_items = self._request_json_get(endpoint_path=endpoint_path, params=params)
            if not isinstance(page_items, list) or not page_items:
                break
            items.extend(page_items)
            page += 1
        return items

    def validate_clone_dir(self, clone_path: Path, overwrite: bool) -> None:
        self.logger.debug(f"validate_clone_dir(clone_path: {clone_path}, overwrite: {overwrite})")
        if clone_path.exists() and not overwrite:
            raise ValueError("Clone directory exists and overwrite is disabled.")
        if not clone_path.exists():
            clone_path.mkdir(parents=True, exist_ok=True)

    def validate_branch_name(self, branch_name: str) -> None:
        self.logger.debug(f"validate_branch_name(branch_name: {branch_name})")
        if not re.match(r"^[a-zA-Z0-9/_-]+$", branch_name):
            raise ValueError("Branch name is invalid.")

    def convert_https_to_ssh(self, https_url: str) -> str:
        self.logger.debug(f"convert_https_to_ssh(https_url: {https_url})")
        if not https_url.startswith("https://"):
            raise ValueError("HTTPS URL format is invalid.")
        url_without_scheme = https_url[8:]
        parts = url_without_scheme.split("/", 1)
        if len(parts) != 2:
            raise ValueError("HTTPS URL format is invalid.")
        domain, path = parts
        ssh_url = f"git@{domain}:{path}"
        self.logger.debug(f"Converted {https_url} to {ssh_url}")
        return ssh_url

    def parse_repo_path(self, ssh_url: str) -> tuple[str, str, str]:
        self.logger.debug(f"parse_repo_path(ssh_url: {ssh_url})")
        match = re.match(r"git@([^:]+):(.+)\.git$", ssh_url)
        if not match:
            raise ValueError("SSH URL format is invalid.")
        domain = match.group(1)
        full_path = match.group(2)
        path_parts = full_path.split("/")
        project = path_parts[-1]
        namespace = "/".join(path_parts[:-1])
        return domain, namespace, project

    def git_clone(self, clone_url: str, project_path: str) -> None:
        self.logger.debug(f"git_clone(clone_url: {clone_url}, project_path: {project_path})")
        subprocess.run(["git", "clone", clone_url, project_path], check=True)

    def get_group_projects(self, group_id: int, include_subgroups: bool = True, archived: bool = False) -> List[Dict[str, Any]]:
        self.logger.debug(f"get_group_projects(group_id: {group_id})")
        params = {"include_subgroups": str(include_subgroups).lower(), "archived": str(archived).lower(), "simple": "true"}
        return self._collect_paginated(endpoint_path=f"/api/v4/groups/{group_id}/projects", base_params=params)

    def get_project(self, project_id: int) -> dict[str, Any]:
        self.logger.debug(f"get_project(project_id: {project_id})")
        project = self._request_json_get(endpoint_path=f"/api/v4/projects/{project_id}")
        if not isinstance(project, dict):
            raise RuntimeError(f"Unexpected GitLab project response for project_id={project_id}.")
        return project

    def get_project_pipelines(self, project_id: int, updated_after: str, updated_before: str, ref: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        self.logger.debug(
            "get_project_pipelines("
            f"project_id: {project_id}, updated_after: {updated_after}, updated_before: {updated_before}, "
            f"ref: {ref}, status: {status})"
        )
        params: dict[str, Any] = {"updated_after": updated_after, "updated_before": updated_before}
        if ref:
            params["ref"] = ref
        if status:
            params["status"] = status
        return self._collect_paginated(endpoint_path=f"/api/v4/projects/{project_id}/pipelines", base_params=params)

    def get_pipeline_jobs(self, project_id: int, pipeline_id: int) -> list[dict[str, Any]]:
        self.logger.debug(f"get_pipeline_jobs(project_id: {project_id}, pipeline_id: {pipeline_id})")
        return self._collect_paginated(endpoint_path=f"/api/v4/projects/{project_id}/pipelines/{pipeline_id}/jobs", base_params={})

    def get_project_commits(self, project_id: int, ref_name: str, since: str | None = None, until: str | None = None) -> list[dict[str, Any]]:
        self.logger.debug(
            f"get_project_commits(project_id: {project_id}, ref_name: {ref_name}, since: {since}, until: {until})"
        )
        params: dict[str, Any] = {"ref_name": ref_name}
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        return self._collect_paginated(endpoint_path=f"/api/v4/projects/{project_id}/repository/commits", base_params=params)

    # created_after is in isoformat, e.g. 2026-02-01T00:00:00+00:00
    def get_group_merge_requests(self, group_id: int, created_after: str, state: str = "all", author_username: Optional[str] = None) -> List[Dict[str, Any]]:
        self.logger.debug(f"get_group_merge_requests(group_id: {group_id}, created_after: {created_after}, state: {state}, author_username: {author_username})")
        headers = {"Private-Token": self.gitlab_token}
        page = 1
        all_merge_requests = []
        while True:
            merge_requests_url = f"{self.gitlab_url}/api/v4/groups/{group_id}/merge_requests"
            params = {
                "include_subgroups": "true",
                "state": state,
                "created_after": created_after,
                "per_page": "100",
                "page": page,
            }
            if author_username:
                params["author_username"] = author_username
            response = requests.get(merge_requests_url, headers=headers, params=params)
            response.raise_for_status()
            merge_requests = response.json()
            if not merge_requests:
                break
            all_merge_requests = all_merge_requests + merge_requests
            page += 1

        return all_merge_requests

    # created_after is in isoformat, e.g. 2026-02-01T00:00:00+00:00
    def get_project_merge_requests(self, project_id: int, created_after: str, state: str = "all", author_username: Optional[str] = None) -> List[Dict[str, Any]]:
        self.logger.debug(f"get_project_merge_requests(project_id: {project_id}, created_after: {created_after}, state: {state}, author_username: {author_username})")

        headers = {"Private-Token": self.gitlab_token}
        page = 1
        all_merge_requests = []
        while True:
            merge_requests_url = f"{self.gitlab_url}/api/v4/projects/{project_id}/merge_requests"
            params = {
                "state": state,
                "created_after": created_after,
                "per_page": "100",
                "page": page,
            }
            if author_username:
                params["author_username"] = author_username
            response = requests.get(merge_requests_url, headers=headers, params=params)
            response.raise_for_status()
            merge_requests = response.json()
            if not merge_requests:
                break
            all_merge_requests = all_merge_requests + merge_requests
            page += 1

        return all_merge_requests

    def clone_group_projects(self, group_id: int, clone_dir: str) -> None:
        self.logger.debug(f"clone_group_projects(group_id: {group_id}, clone_dir: {clone_dir})")
        projects = self.get_group_projects(group_id)
        for project in projects:
            clone_url = project["ssh_url_to_repo"]
            project_path = os.path.join(clone_dir, project["path_with_namespace"])
            if not os.path.exists(project_path):
                self.logger.info(f"Cloning {project['name']}...")
                time.sleep(2)
                self.git_clone(clone_url, project_path)
            else:
                self.logger.info(f"{project_path} already exists in {clone_dir}. Skipping clone.")
        total_number_of_projects = len(projects)
        self.logger.info(f"Total number of projects: {total_number_of_projects}")

    def test_ssh_connectivity(self, domain: str) -> bool:
        self.logger.debug(f"test_ssh_connectivity(domain: {domain})")
        result = subprocess.run(["ssh", "-T", f"git@{domain}"], capture_output=True, text=True, timeout=10)
        if result.returncode in [0, 1]:
            self.logger.debug(f"SSH connectivity test successful for domain {domain}")
            return True
        self.logger.error(f"SSH connectivity test failed for domain {domain}: {result.stderr}")
        return False

    def clone_repository(self, ssh_url: str, target_path: str) -> None:
        self.logger.debug(f"clone_repository(ssh_url: {ssh_url}, target_path: {target_path})")
        if os.path.exists(target_path):
            self.logger.info(f"Repository already exists at {target_path}. Skipping clone.")
            return
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        self.logger.info(f"Cloning {ssh_url} to {target_path}")
        subprocess.run(["git", "clone", ssh_url, target_path], check=True, capture_output=True, text=True)
        self.logger.debug(f"Successfully cloned repository to {target_path}")

    def check_git_status(self, repo_path: str) -> tuple[bool, str]:
        self.logger.debug(f"check_git_status(repo_path: {repo_path})")
        status_result = subprocess.run(["git", "status", "--porcelain"], cwd=repo_path, capture_output=True, text=True, check=True)
        is_clean = len(status_result.stdout.strip()) == 0
        branch_result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path, capture_output=True, text=True, check=True)
        current_branch = branch_result.stdout.strip()
        self.logger.debug(f"Repository status: clean={is_clean}, branch={current_branch}")
        return is_clean, current_branch

    def create_branch(self, repo_path: str, branch_name: str) -> None:
        self.logger.debug(f"create_branch(repo_path: {repo_path}, branch_name: {branch_name})")
        subprocess.run(["git", "checkout", "-b", branch_name], cwd=repo_path, check=True, capture_output=True, text=True)
        self.logger.debug(f"Created and checked out branch {branch_name}")

    def push_branch(self, repo_path: str, branch_name: str) -> None:
        self.logger.debug(f"push_branch(repo_path: {repo_path}, branch_name: {branch_name})")
        subprocess.run(["git", "push", "-u", "origin", branch_name], cwd=repo_path, check=True, capture_output=True, text=True)
        self.logger.info(f"Successfully pushed branch {branch_name} to origin")
