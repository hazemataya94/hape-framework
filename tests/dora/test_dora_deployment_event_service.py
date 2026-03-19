from datetime import datetime, timezone

import pytest

from services.dora_deployment_event_service import DoraDeploymentEventService
from services.dora_models import DoraDeploymentEvent, DoraProjectRule


def _build_rule() -> DoraProjectRule:
    return DoraProjectRule(
        provider="gitlab",
        group_path="example/platform",
        project_path="example/platform/service-a",
        project_id=1,
        default_branch="main",
        refs=["main"],
        environment="production",
        successful_job_statuses=["success"],
        deploy_job_names=["deploy-prod"],
        deploy_job_name_regex=["^release-.*$"],
        deploy_stages=["deploy"],
        failure_detection_minutes=60,
        recovery_timeout_minutes=240,
        recovery_stability_minutes=10,
    )


def _build_event(job_name: str, status: str, stage: str, ref: str) -> DoraDeploymentEvent:
    now = datetime.now(timezone.utc)
    return DoraDeploymentEvent(
        provider="gitlab",
        group_path="example/platform",
        project_path="example/platform/service-a",
        project_id=1,
        default_branch="main",
        environment="production",
        pipeline_id=1,
        job_id=2,
        job_name=job_name,
        stage=stage,
        ref=ref,
        sha="abc123",
        status=status,
        started_at=now,
        finished_at=now,
    )


def test_filters_events_by_status_ref_job_and_stage() -> None:
    service = DoraDeploymentEventService()
    rule = _build_rule()
    events = [
        _build_event(job_name="deploy-prod", status="success", stage="deploy", ref="main"),
        _build_event(job_name="release-prod", status="success", stage="deploy", ref="main"),
        _build_event(job_name="test", status="success", stage="test", ref="main"),
        _build_event(job_name="deploy-prod", status="failed", stage="deploy", ref="main"),
        _build_event(job_name="deploy-prod", status="success", stage="deploy", ref="feature-branch"),
    ]
    filtered = service.filter_successful_deployment_events(events=events, rule=rule)
    assert len(filtered) == 2
    assert all(item.status == "success" for item in filtered)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
