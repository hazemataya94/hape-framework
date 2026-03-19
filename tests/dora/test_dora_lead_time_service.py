from datetime import datetime, timedelta, timezone

import pytest

from services.dora_lead_time_service import DoraLeadTimeService
from services.dora_models import DoraDeploymentEvent


def _build_event(finished_at: datetime, sha: str) -> DoraDeploymentEvent:
    return DoraDeploymentEvent(
        provider="gitlab",
        group_path="example/platform",
        project_path="example/platform/service-a",
        project_id=1,
        default_branch="main",
        environment="production",
        pipeline_id=1,
        job_id=2,
        job_name="deploy",
        stage="deploy",
        ref="main",
        sha=sha,
        status="success",
        started_at=finished_at - timedelta(minutes=1),
        finished_at=finished_at,
    )


def test_calculate_project_lead_time_seconds_for_commit_ranges() -> None:
    now = datetime.now(timezone.utc)
    events = [_build_event(now - timedelta(hours=2), "sha-1"), _build_event(now, "sha-2")]
    commits = [
        {"id": "sha-1", "committed_date": (now - timedelta(hours=2, minutes=10)).isoformat()},
        {"id": "sha-a", "committed_date": (now - timedelta(hours=1, minutes=30)).isoformat()},
        {"id": "sha-b", "committed_date": (now - timedelta(hours=1)).isoformat()},
        {"id": "sha-2", "committed_date": (now - timedelta(minutes=50)).isoformat()},
    ]
    service = DoraLeadTimeService()
    lead_time_seconds, has_change_data = service.calculate_project_lead_time_seconds(deployment_events=events, commits=commits)
    assert has_change_data == 1
    assert lead_time_seconds > 0


def test_calculate_project_lead_time_seconds_handles_no_change_data() -> None:
    now = datetime.now(timezone.utc)
    events = [_build_event(now - timedelta(hours=1), "sha-1"), _build_event(now, "sha-1")]
    commits = [{"id": "sha-1", "committed_date": (now - timedelta(hours=2)).isoformat()}]
    service = DoraLeadTimeService()
    lead_time_seconds, has_change_data = service.calculate_project_lead_time_seconds(deployment_events=events, commits=commits)
    assert lead_time_seconds == 0.0
    assert has_change_data == 0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
