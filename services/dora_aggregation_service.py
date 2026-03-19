from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from core.logging import LocalLogging
from services.dora_models import DoraDeploymentEvent, DoraFailureEvent, DoraProjectInfo, DoraProjectRule, DoraProjectWindowMetrics


class DoraAggregationService:
    SUPPORTED_WINDOWS_DAYS = {"7d": 7, "30d": 30, "90d": 90}

    def __init__(self) -> None:
        self.logger = LocalLogging.get_logger("hape.dora_aggregation_service")

    @staticmethod
    def _is_in_window(ts: datetime, window_days: int) -> bool:
        return ts >= (datetime.now(timezone.utc) - timedelta(days=window_days))

    @staticmethod
    def _aggregate_recovery_time_seconds(failure_events: list[DoraFailureEvent]) -> tuple[float, int]:
        recovery_samples = [
            (item.recovered_at - item.failure_started_at).total_seconds()
            for item in failure_events
            if item.recovered_at is not None and item.recovered_at >= item.failure_started_at
        ]
        if not recovery_samples:
            return 0.0, 0
        return sum(recovery_samples) / len(recovery_samples), 1

    def build_project_window_metrics(
        self,
        projects_by_path: dict[str, DoraProjectInfo],
        rules_by_project_path: dict[str, DoraProjectRule],
        deployment_events_by_project_path: dict[str, list[DoraDeploymentEvent]],
        lead_time_seconds_by_project_path: dict[str, tuple[float, int]],
        failure_events_by_project_path: dict[str, list[DoraFailureEvent]],
    ) -> list[DoraProjectWindowMetrics]:
        rows: list[DoraProjectWindowMetrics] = []
        for window, window_days in self.SUPPORTED_WINDOWS_DAYS.items():
            for project_path, project in projects_by_path.items():
                rule = rules_by_project_path[project_path]
                project_events = deployment_events_by_project_path.get(project_path, [])
                project_events_window = [event for event in project_events if self._is_in_window(ts=event.finished_at, window_days=window_days)]
                project_failures = failure_events_by_project_path.get(project_path, [])
                project_failures_window = [
                    failure for failure in project_failures if self._is_in_window(ts=failure.deployment_finished_at, window_days=window_days)
                ]
                deployments_total = len(project_events_window)
                failed_deployments_total = len(project_failures_window)
                change_fail_rate_ratio = 0.0 if deployments_total == 0 else failed_deployments_total / deployments_total
                recovery_time_seconds, has_recovery_data = self._aggregate_recovery_time_seconds(failure_events=project_failures_window)
                lead_time_seconds, has_change_data = lead_time_seconds_by_project_path.get(project_path, (0.0, 0))
                rows.append(
                    DoraProjectWindowMetrics(
                        provider=project.provider,
                        group_path=project.group_path,
                        project_path=project.project_path,
                        default_branch=project.default_branch,
                        archived=project.archived,
                        environment=rule.environment,
                        window=window,
                        deployments_total=deployments_total,
                        has_deployments=1 if deployments_total > 0 else 0,
                        deployment_frequency_per_day=deployments_total / float(window_days),
                        lead_time_seconds=lead_time_seconds,
                        has_change_data=has_change_data,
                        failed_deployments_total=failed_deployments_total,
                        change_fail_rate_ratio=change_fail_rate_ratio,
                        failed_deployment_recovery_time_seconds=recovery_time_seconds if has_recovery_data else 0.0,
                        open_failed_deployments_total=sum(1 for item in project_failures_window if item.is_open),
                    )
                )
        return rows

    def build_rollups(self, project_rows: list[DoraProjectWindowMetrics]) -> dict[str, dict[str, dict[str, float]]]:
        rollups: dict[str, dict[str, dict[str, float]]] = {"overview": defaultdict(dict), "group": defaultdict(dict), "project": defaultdict(dict)}
        for row in project_rows:
            key_base = f"{row.provider}|{row.environment}|{row.window}"
            overview_key = key_base
            group_key = f"{key_base}|{row.group_path}"
            project_key = f"{group_key}|{row.project_path}"
            rollups["overview"][overview_key] = {
                "projects_total": rollups["overview"].get(overview_key, {}).get("projects_total", 0.0) + 1.0,
                "projects_with_deploy_data": rollups["overview"].get(overview_key, {}).get("projects_with_deploy_data", 0.0) + float(row.has_deployments),
            }
            rollups["group"][group_key] = {
                "projects_total": rollups["group"].get(group_key, {}).get("projects_total", 0.0) + 1.0,
                "projects_with_deploy_data": rollups["group"].get(group_key, {}).get("projects_with_deploy_data", 0.0) + float(row.has_deployments),
            }
            rollups["project"][project_key] = {
                "deployments_total": float(row.deployments_total),
                "deployment_frequency_per_day": row.deployment_frequency_per_day,
                "lead_time_seconds": row.lead_time_seconds,
                "change_fail_rate_ratio": row.change_fail_rate_ratio,
                "failed_deployment_recovery_time_seconds": row.failed_deployment_recovery_time_seconds,
            }
        return rollups


if __name__ == "__main__":
    print(DoraAggregationService.SUPPORTED_WINDOWS_DAYS)
