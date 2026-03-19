from __future__ import annotations

from datetime import datetime, timedelta, timezone

from clients.gitlab_client import GitLabClient
from core.errors.exceptions import HapeExternalError, HapeValidationError
from core.errors.messages.dora_error_messages import get_dora_error_message
from core.logging import LocalLogging
from services.dora_models import DoraDeploymentEvent, DoraProjectInfo, DoraProjectRule
from utils.datetime_utils import DatetimeUtils


class DoraGitLabProviderService:
    def __init__(self, gitlab_client: GitLabClient | None = None) -> None:
        self.gitlab_client = gitlab_client or GitLabClient()
        self.logger = LocalLogging.get_logger("hape.dora_git_lab_provider_service")

    @staticmethod
    def _resolve_window_timestamps(window_days: int) -> tuple[str, str]:
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=window_days)
        return start.isoformat(), now.isoformat()

    @staticmethod
    def _resolve_group_id(raw_group_id: str) -> int:
        try:
            return int(str(raw_group_id).strip())
        except (TypeError, ValueError) as exc:
            raise HapeValidationError(
                code="DORA_CONFIG_INVALID_SCHEMA",
                message=get_dora_error_message("DORA_CONFIG_INVALID_SCHEMA", reason=f"Invalid group id '{raw_group_id}'"),
            ) from exc

    @staticmethod
    def _to_deployment_event(project: DoraProjectInfo, rule: DoraProjectRule, pipeline: dict, job: dict) -> DoraDeploymentEvent:
        started_at = DatetimeUtils.parse_iso_datetime(str(job.get("started_at") or pipeline.get("created_at")))
        finished_at = DatetimeUtils.parse_iso_datetime(str(job.get("finished_at") or job.get("created_at") or pipeline.get("updated_at")))
        return DoraDeploymentEvent(
            provider=rule.provider,
            group_path=project.group_path,
            project_path=project.project_path,
            project_id=project.project_id,
            default_branch=project.default_branch,
            environment=rule.environment,
            pipeline_id=int(pipeline.get("id")),
            job_id=int(job.get("id")),
            job_name=str(job.get("name", "")),
            stage=str(job.get("stage", "")),
            ref=str(job.get("ref", "")),
            sha=str(job.get("commit", {}).get("id", "") or pipeline.get("sha", "")),
            status=str(job.get("status", "")),
            started_at=started_at,
            finished_at=finished_at,
        )

    def fetch_projects_for_group_ids(self, group_ids: list[str], project_rules: dict[str, DoraProjectRule]) -> dict[str, DoraProjectInfo]:
        projects_by_path: dict[str, DoraProjectInfo] = {}
        for raw_group_id in group_ids:
            group_id = self._resolve_group_id(raw_group_id)
            try:
                projects = self.gitlab_client.get_group_projects(group_id=group_id, include_subgroups=True, archived=False)
            except Exception as exc:
                raise HapeExternalError(
                    code="DORA_GITLAB_FETCH_FAILED",
                    message=get_dora_error_message("DORA_GITLAB_FETCH_FAILED", group_id=str(group_id)),
                ) from exc
            for project in projects:
                project_path = str(project.get("path_with_namespace", "")).strip()
                if project_path not in project_rules:
                    continue
                rule = project_rules[project_path]
                projects_by_path[project_path] = DoraProjectInfo(
                    provider=rule.provider,
                    group_path=rule.group_path,
                    project_path=project_path,
                    project_id=int(project.get("id", 0)),
                    default_branch=str(project.get("default_branch", rule.default_branch)),
                    archived=bool(project.get("archived", False)),
                )
        for project_path, rule in project_rules.items():
            if project_path in projects_by_path:
                continue
            if rule.project_id is None:
                continue
            projects_by_path[project_path] = DoraProjectInfo(
                provider=rule.provider,
                group_path=rule.group_path,
                project_path=rule.project_path,
                project_id=rule.project_id,
                default_branch=rule.default_branch,
                archived=False,
            )
        return projects_by_path

    def fetch_project_deployment_jobs(self, project: DoraProjectInfo, rule: DoraProjectRule, window_days: int) -> list[DoraDeploymentEvent]:
        updated_after, updated_before = self._resolve_window_timestamps(window_days=window_days)
        pipelines = self.gitlab_client.get_project_pipelines(
            project_id=project.project_id,
            updated_after=updated_after,
            updated_before=updated_before,
            ref=None,
            status=None,
        )
        deployment_events: list[DoraDeploymentEvent] = []
        for pipeline in pipelines:
            pipeline_id = int(pipeline.get("id", 0))
            if not pipeline_id:
                continue
            jobs = self.gitlab_client.get_pipeline_jobs(project_id=project.project_id, pipeline_id=pipeline_id)
            for job in jobs:
                deployment_events.append(self._to_deployment_event(project=project, rule=rule, pipeline=pipeline, job=job))
        deployment_events.sort(key=lambda item: item.finished_at)
        return deployment_events

    def fetch_project_commits(self, project: DoraProjectInfo, ref_name: str, since: str | None = None, until: str | None = None) -> list[dict]:
        return self.gitlab_client.get_project_commits(
            project_id=project.project_id,
            ref_name=ref_name,
            since=since,
            until=until,
        )


if __name__ == "__main__":
    print(DoraGitLabProviderService)
