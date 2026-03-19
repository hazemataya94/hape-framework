from datetime import datetime, timedelta, timezone

import pytest

from services.dora_failure_service import DoraFailureService
from services.dora_models import DoraDeploymentEvent, DoraKubernetesMapping, DoraProjectRule, DoraWorkloadMapping


class _FakePrometheusClient:
    def query_range(self, promql: str, start: datetime, end: datetime, step: str) -> dict:
        samples = [
            [start.timestamp(), "0"],
            [(start + timedelta(minutes=5)).timestamp(), "1"],
            [(start + timedelta(minutes=15)).timestamp(), "1"],
            [(start + timedelta(minutes=25)).timestamp(), "0"],
            [(start + timedelta(minutes=35)).timestamp(), "0"],
            [(start + timedelta(minutes=45)).timestamp(), "0"],
        ]
        return {"status": "success", "data": {"result": [{"values": samples}]}}


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
        deploy_job_name_regex=[],
        deploy_stages=["deploy"],
        failure_detection_minutes=60,
        recovery_timeout_minutes=240,
        recovery_stability_minutes=10,
    )


def _build_event() -> DoraDeploymentEvent:
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
        job_name="deploy-prod",
        stage="deploy",
        ref="main",
        sha="abc123",
        status="success",
        started_at=now - timedelta(minutes=1),
        finished_at=now,
    )


def test_evaluate_failures_detects_failure_and_recovery() -> None:
    service = DoraFailureService(prometheus_client=_FakePrometheusClient())
    mapping = DoraKubernetesMapping(
        provider="gitlab",
        project_path="example/platform/service-a",
        cluster="kind-hape",
        namespace="payments",
        workloads=[DoraWorkloadMapping(kind="Deployment", name="service-a", prometheus_label_matchers={"deployment": "service-a"})],
    )
    results = service.evaluate_failures(
        deployment_events=[_build_event()],
        project_rule=_build_rule(),
        kubernetes_mapping=mapping,
        prometheus_url="http://localhost:9090",
    )
    assert len(results) == 1
    assert results[0].failure_started_at is not None
    assert results[0].recovered_at is not None
    assert results[0].is_open is False


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
