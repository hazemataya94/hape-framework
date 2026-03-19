from datetime import datetime, timedelta, timezone

import pytest

from services.dora_github_provider_service import DoraGithubProviderService
from services.dora_models import DoraProjectRule


class _FakeGithubClient:
    def get_org_repositories(self, org_name: str, include_archived: bool = False) -> list[dict]:
        return [
            {"id": 21, "full_name": "example-org/service-a", "default_branch": "main", "archived": False},
            {"id": 22, "full_name": "example-org/service-b", "default_branch": "main", "archived": False},
        ]

    def get_repository_workflow_runs(
        self,
        owner: str,
        repo: str,
        created_after: str,
        created_before: str,
        branch: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        now = datetime.now(timezone.utc)
        return [{"id": 201, "head_sha": "sha-1", "head_branch": "main", "created_at": (now - timedelta(minutes=20)).isoformat(), "updated_at": now.isoformat()}]

    def get_workflow_run_jobs(self, owner: str, repo: str, run_id: int) -> list[dict]:
        now = datetime.now(timezone.utc)
        return [
            {
                "id": 701,
                "name": "deploy-prod",
                "step_name": "deploy",
                "conclusion": "success",
                "started_at": (now - timedelta(minutes=5)).isoformat(),
                "completed_at": now.isoformat(),
            }
        ]

    def get_repository_commits(self, owner: str, repo: str, sha: str, since: str | None = None, until: str | None = None) -> list[dict]:
        return [{"sha": "sha-1", "commit": {"committer": {"date": datetime.now(timezone.utc).isoformat()}}}]


def _build_rules() -> dict[str, DoraProjectRule]:
    return {
        "example-org/service-a": DoraProjectRule(
            provider="github",
            group_path="example-org",
            project_path="example-org/service-a",
            project_id=21,
            default_branch="main",
            refs=["main"],
            environment="production",
            successful_job_statuses=["success"],
            deploy_job_names=["deploy-prod"],
            deploy_job_name_regex=[],
            deploy_stages=[],
            failure_detection_minutes=60,
            recovery_timeout_minutes=240,
            recovery_stability_minutes=10,
        )
    }


def test_fetch_projects_for_github_orgs() -> None:
    service = DoraGithubProviderService(github_client=_FakeGithubClient())
    projects = service.fetch_projects_for_group_ids(group_ids=["example-org"], project_rules=_build_rules())
    assert "example-org/service-a" in projects
    assert projects["example-org/service-a"].project_id == 21


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
