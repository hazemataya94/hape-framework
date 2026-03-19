from __future__ import annotations

from datetime import datetime, timedelta, timezone

from clients.github_client import GitHubClient
from core.errors.exceptions import HapeExternalError, HapeValidationError
from core.errors.messages.dora_error_messages import get_dora_error_message
from core.logging import LocalLogging
from services.dora_models import DoraDeploymentEvent, DoraProjectInfo, DoraProjectRule
from utils.datetime_utils import DatetimeUtils


class DoraGithubProviderService:
    def __init__(self, github_client: GitHubClient | None = None) -> None:
        self.github_client = github_client or GitHubClient()
        self.logger = LocalLogging.get_logger("hape.dora_github_provider_service")

    @staticmethod
    def _normalize_scope(raw_scope: str) -> str:
        scope = str(raw_scope).strip()
        if not scope:
            raise HapeValidationError(
                code="DORA_CONFIG_INVALID_SCHEMA",
                message=get_dora_error_message("DORA_CONFIG_INVALID_SCHEMA", reason="GitHub organization is empty."),
            )
        return scope

    @staticmethod
    def _resolve_window_timestamps(window_days: int) -> tuple[str, str]:
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=window_days)
        return start.isoformat(), now.isoformat()

    @staticmethod
    def _to_deployment_event(project: DoraProjectInfo, rule: DoraProjectRule, run: dict, job: dict) -> DoraDeploymentEvent:
        started_at = DatetimeUtils.parse_iso_datetime(str(job.get("started_at") or run.get("created_at")))
        finished_at = DatetimeUtils.parse_iso_datetime(str(job.get("completed_at") or run.get("updated_at")))
        return DoraDeploymentEvent(
            provider=rule.provider,
            group_path=project.group_path,
            project_path=project.project_path,
            project_id=project.project_id,
            default_branch=project.default_branch,
            environment=rule.environment,
            pipeline_id=int(run.get("id", 0)),
            job_id=int(job.get("id", 0)),
            job_name=str(job.get("name", "")),
            stage=str(job.get("step_name", "")),
            ref=str(run.get("head_branch", "")),
            sha=str(run.get("head_sha", "")),
            status="success" if str(job.get("conclusion", "")).lower() == "success" else str(job.get("conclusion", "")),
            started_at=started_at,
            finished_at=finished_at,
        )

    @staticmethod
    def _split_owner_repo(project_path: str) -> tuple[str, str]:
        owner, repo = project_path.split("/", 1)
        return owner, repo

    def fetch_project_commits(self, project: DoraProjectInfo, ref_name: str, since: str | None = None, until: str | None = None) -> list[dict]:
        owner, repo = self._split_owner_repo(project.project_path)
        commits = self.github_client.get_repository_commits(owner=owner, repo=repo, sha=ref_name, since=since, until=until)
        normalized: list[dict] = []
        for commit in commits:
            commit_sha = str(commit.get("sha", "")).strip()
            committed_date = str(commit.get("commit", {}).get("committer", {}).get("date", "")).strip()
            if not commit_sha or not committed_date:
                continue
            normalized.append({"id": commit_sha, "committed_date": committed_date})
        return normalized

    def fetch_projects_for_group_ids(self, group_ids: list[str], project_rules: dict[str, DoraProjectRule]) -> dict[str, DoraProjectInfo]:
        projects_by_path: dict[str, DoraProjectInfo] = {}
        for raw_scope in group_ids:
            org_name = self._normalize_scope(raw_scope=raw_scope)
            try:
                repositories = self.github_client.get_org_repositories(org_name=org_name, include_archived=False)
            except Exception as exc:
                raise HapeExternalError(
                    code="DORA_GITHUB_FETCH_FAILED",
                    message=get_dora_error_message("DORA_GITHUB_FETCH_FAILED", scope=org_name),
                ) from exc
            for repository in repositories:
                project_path = str(repository.get("full_name", "")).strip()
                if project_path not in project_rules:
                    continue
                rule = project_rules[project_path]
                projects_by_path[project_path] = DoraProjectInfo(
                    provider="github",
                    group_path=org_name,
                    project_path=project_path,
                    project_id=int(repository.get("id", 0)),
                    default_branch=str(repository.get("default_branch", "main")),
                    archived=bool(repository.get("archived", False)),
                )
        for project_path, rule in project_rules.items():
            if project_path in projects_by_path:
                continue
            if rule.provider != "github":
                continue
            if rule.project_id is None:
                continue
            projects_by_path[project_path] = DoraProjectInfo(
                provider="github",
                group_path=rule.group_path,
                project_path=project_path,
                project_id=rule.project_id,
                default_branch=rule.default_branch,
                archived=False,
            )
        return projects_by_path

    def fetch_project_deployment_jobs(self, project: DoraProjectInfo, rule: DoraProjectRule, window_days: int) -> list[DoraDeploymentEvent]:
        created_after, created_before = self._resolve_window_timestamps(window_days=window_days)
        owner, repo = self._split_owner_repo(project.project_path)
        workflow_runs = self.github_client.get_repository_workflow_runs(
            owner=owner,
            repo=repo,
            created_after=created_after,
            created_before=created_before,
            branch=None,
            status="completed",
        )
        deployment_events: list[DoraDeploymentEvent] = []
        for run in workflow_runs:
            run_id = int(run.get("id", 0))
            if not run_id:
                continue
            jobs = self.github_client.get_workflow_run_jobs(owner=owner, repo=repo, run_id=run_id)
            for job in jobs:
                deployment_events.append(self._to_deployment_event(project=project, rule=rule, run=run, job=job))
        deployment_events.sort(key=lambda item: item.finished_at)
        return deployment_events


if __name__ == "__main__":
    print(DoraGithubProviderService)
