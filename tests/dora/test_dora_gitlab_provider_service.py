from datetime import datetime, timedelta, timezone

import pytest

from services.dora_gitlab_provider_service import DoraGitLabProviderService
from services.dora_models import DoraProjectRule


class _FakeGitLabClient:
    def get_group_projects(self, group_id: int, include_subgroups: bool = True, archived: bool = False) -> list[dict]:
        return [
            {"id": 11, "path_with_namespace": "example/platform/service-a", "default_branch": "main", "archived": False},
            {"id": 12, "path_with_namespace": "example/platform/service-b", "default_branch": "main", "archived": False},
        ]

    def get_project_pipelines(self, project_id: int, updated_after: str, updated_before: str, ref: str | None = None, status: str | None = None) -> list[dict]:
        now = datetime.now(timezone.utc)
        return [{"id": 101, "sha": "sha-1", "created_at": (now - timedelta(minutes=30)).isoformat(), "updated_at": now.isoformat()}]

    def get_pipeline_jobs(self, project_id: int, pipeline_id: int) -> list[dict]:
        now = datetime.now(timezone.utc)
        return [
            {
                "id": 501,
                "name": "deploy-prod",
                "stage": "deploy",
                "status": "success",
                "ref": "main",
                "started_at": (now - timedelta(minutes=5)).isoformat(),
                "finished_at": now.isoformat(),
                "created_at": (now - timedelta(minutes=6)).isoformat(),
                "commit": {"id": "sha-1"},
            }
        ]

    def get_project_commits(self, project_id: int, ref_name: str, since: str | None = None, until: str | None = None) -> list[dict]:
        return [{"id": "sha-1", "committed_date": datetime.now(timezone.utc).isoformat()}]


def _build_rules() -> dict[str, DoraProjectRule]:
    return {
        "example/platform/service-a": DoraProjectRule(
            provider="gitlab",
            group_path="example/platform",
            project_path="example/platform/service-a",
            project_id=11,
            default_branch="main",
            refs=["main"],
            environment="production",
            successful_job_statuses=["success"],
            deploy_job_names=["deploy-prod"],
            deploy_job_name_regex=[],
            deploy_stages=["deploy"],
            failure_detection_minutes=60,
            recovery_timeout_minutes=240,
            recovery_stability_minutes=10,
        )
    }


def test_fetch_projects_for_group_ids_includes_configured_projects() -> None:
    service = DoraGitLabProviderService(gitlab_client=_FakeGitLabClient())
    projects = service.fetch_projects_for_group_ids(group_ids=["123"], project_rules=_build_rules())
    assert "example/platform/service-a" in projects
    assert projects["example/platform/service-a"].project_id == 11


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
