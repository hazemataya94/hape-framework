from __future__ import annotations

from datetime import datetime, timedelta, timezone

from clients.prometheus_client import PrometheusClient
from core.errors.exceptions import HapeExternalError
from core.errors.messages.dora_error_messages import get_dora_error_message
from core.logging import LocalLogging
from services.dora_models import DoraDeploymentEvent, DoraFailureEvent, DoraKubernetesMapping, DoraProjectRule


class DoraFailureService:
    def __init__(self, prometheus_client: PrometheusClient | None = None) -> None:
        self.prometheus_client = prometheus_client
        self.logger = LocalLogging.get_logger("hape.dora_failure_service")

    @staticmethod
    def _build_matcher(labels: dict[str, str]) -> str:
        parts = [f'{key}="{value}"' for key, value in sorted(labels.items())]
        return ",".join(parts)

    @staticmethod
    def _build_failure_promql(labels: dict[str, str]) -> str:
        matcher = DoraFailureService._build_matcher(labels=labels)
        unavailable = f"max(kube_deployment_status_replicas_unavailable{{{matcher}}})"
        not_ready = f"max(kube_pod_status_ready{{condition=\"false\",{matcher}}})"
        crashloop = f"max(kube_pod_container_status_waiting_reason{{reason=\"CrashLoopBackOff\",{matcher}}})"
        restart_increase = f"max(increase(kube_pod_container_status_restarts_total{{{matcher}}}[5m]))"
        return f"({unavailable}) or ({not_ready}) or ({crashloop}) or ({restart_increase})"

    @staticmethod
    def _extract_series_values(response: dict) -> list[tuple[datetime, float]]:
        result = response.get("data", {}).get("result", [])
        values: list[tuple[datetime, float]] = []
        for series in result:
            for raw_value in series.get("values", []):
                if len(raw_value) != 2:
                    continue
                timestamp = datetime.fromtimestamp(float(raw_value[0]), tz=timezone.utc)
                sample = float(raw_value[1])
                values.append((timestamp, sample))
        values.sort(key=lambda item: item[0])
        return values

    @staticmethod
    def _find_failure_started(values: list[tuple[datetime, float]]) -> datetime | None:
        for timestamp, sample in values:
            if sample > 0:
                return timestamp
        return None

    @staticmethod
    def _find_recovered_at(values: list[tuple[datetime, float]], failure_started_at: datetime, stability_minutes: int) -> datetime | None:
        if not values:
            return None
        stable_seconds_required = stability_minutes * 60
        stable_since: datetime | None = None
        for timestamp, sample in values:
            if timestamp < failure_started_at:
                continue
            if sample > 0:
                stable_since = None
                continue
            if stable_since is None:
                stable_since = timestamp
            stable_seconds = (timestamp - stable_since).total_seconds()
            if stable_seconds >= stable_seconds_required:
                return timestamp
        return None

    def evaluate_failures(
        self,
        deployment_events: list[DoraDeploymentEvent],
        project_rule: DoraProjectRule,
        kubernetes_mapping: DoraKubernetesMapping | None,
        prometheus_url: str,
    ) -> list[DoraFailureEvent]:
        if not deployment_events or kubernetes_mapping is None:
            return []
        if self.prometheus_client is None:
            self.prometheus_client = PrometheusClient(base_url=prometheus_url)
        failure_events: list[DoraFailureEvent] = []
        for event in deployment_events:
            detection_window_end = event.finished_at + timedelta(minutes=project_rule.failure_detection_minutes)
            recovery_deadline = event.finished_at + timedelta(minutes=project_rule.recovery_timeout_minutes)
            series_values: list[tuple[datetime, float]] = []
            for workload in kubernetes_mapping.workloads:
                try:
                    promql = self._build_failure_promql(labels=workload.prometheus_label_matchers)
                    query_result = self.prometheus_client.query_range(
                        promql=promql,
                        start=event.finished_at,
                        end=recovery_deadline,
                        step="60s",
                    )
                except Exception as exc:
                    raise HapeExternalError(
                        code="DORA_PROMETHEUS_QUERY_FAILED",
                        message=get_dora_error_message("DORA_PROMETHEUS_QUERY_FAILED", project_path=event.project_path),
                    ) from exc
                series_values.extend(self._extract_series_values(response=query_result))
            series_values.sort(key=lambda item: item[0])
            failure_started_at = self._find_failure_started(values=[item for item in series_values if item[0] <= detection_window_end])
            if failure_started_at is None:
                continue
            recovered_at = self._find_recovered_at(
                values=[item for item in series_values if failure_started_at <= item[0] <= recovery_deadline],
                failure_started_at=failure_started_at,
                stability_minutes=project_rule.recovery_stability_minutes,
            )
            failure_events.append(
                DoraFailureEvent(
                    project_path=event.project_path,
                    environment=event.environment,
                    deployment_finished_at=event.finished_at,
                    failure_started_at=failure_started_at,
                    recovered_at=recovered_at,
                    is_open=recovered_at is None,
                )
            )
        return failure_events


if __name__ == "__main__":
    print(DoraFailureService)
