from datetime import datetime, timedelta, timezone

import pytest

from services.dora_aggregation_service import DoraAggregationService
from services.dora_models import DoraDeploymentEvent, DoraFailureEvent, DoraProjectInfo, DoraProjectRule


def _build_project_info(project_path: str) -> DoraProjectInfo:
    return DoraProjectInfo(
        provider="gitlab",
        group_path="example/platform",
        project_path=project_path,
        project_id=1,
        default_branch="main",
        archived=False,
    )


def _build_rule(project_path: str) -> DoraProjectRule:
    return DoraProjectRule(
        provider="gitlab",
        group_path="example/platform",
        project_path=project_path,
        project_id=1,
        default_branch="main",
        refs=["main"],
        environment="production",
        successful_job_statuses=["success"],
        deploy_job_names=["deploy"],
        deploy_job_name_regex=[],
        deploy_stages=["deploy"],
        failure_detection_minutes=60,
        recovery_timeout_minutes=240,
        recovery_stability_minutes=10,
    )


def _build_event(project_path: str) -> DoraDeploymentEvent:
    now = datetime.now(timezone.utc)
    return DoraDeploymentEvent(
        provider="gitlab",
        group_path="example/platform",
        project_path=project_path,
        project_id=1,
        default_branch="main",
        environment="production",
        pipeline_id=1,
        job_id=2,
        job_name="deploy",
        stage="deploy",
        ref="main",
        sha="sha-1",
        status="success",
        started_at=now - timedelta(minutes=1),
        finished_at=now,
    )


def test_build_project_window_metrics_includes_zero_deploy_projects() -> None:
    service = DoraAggregationService()
    projects = {
        "example/platform/service-a": _build_project_info("example/platform/service-a"),
        "example/platform/service-b": _build_project_info("example/platform/service-b"),
    }
    rules = {
        "example/platform/service-a": _build_rule("example/platform/service-a"),
        "example/platform/service-b": _build_rule("example/platform/service-b"),
    }
    deployment_events = {"example/platform/service-a": [_build_event("example/platform/service-a")]}
    lead_times = {"example/platform/service-a": (120.0, 1), "example/platform/service-b": (0.0, 0)}
    failure_events = {
        "example/platform/service-a": [
            DoraFailureEvent(
                project_path="example/platform/service-a",
                environment="production",
                deployment_finished_at=datetime.now(timezone.utc),
                failure_started_at=datetime.now(timezone.utc) - timedelta(minutes=20),
                recovered_at=datetime.now(timezone.utc) - timedelta(minutes=10),
                is_open=False,
            )
        ]
    }
    rows = service.build_project_window_metrics(
        projects_by_path=projects,
        rules_by_project_path=rules,
        deployment_events_by_project_path=deployment_events,
        lead_time_seconds_by_project_path=lead_times,
        failure_events_by_project_path=failure_events,
    )
    rows_by_project = {(row.project_path, row.window): row for row in rows}
    assert rows_by_project[("example/platform/service-b", "7d")].deployments_total == 0
    assert rows_by_project[("example/platform/service-b", "7d")].has_deployments == 0
    assert rows_by_project[("example/platform/service-a", "7d")].deployments_total == 1


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
