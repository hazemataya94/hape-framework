from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from core.config import Config
from core.logging import LocalLogging
from services.dora_aggregation_service import DoraAggregationService
from services.dora_config_service import DoraConfigService
from services.dora_deployment_event_service import DoraDeploymentEventService
from services.dora_failure_service import DoraFailureService
from services.dora_github_provider_service import DoraGithubProviderService
from services.dora_gitlab_provider_service import DoraGitLabProviderService
from services.dora_lead_time_service import DoraLeadTimeService


class DoraService:
    DEFAULT_MAX_PROJECT_WORKERS = 6

    def __init__(
        self,
        config_service: DoraConfigService | None = None,
        provider_service: DoraGitLabProviderService | DoraGithubProviderService | None = None,
        deployment_event_service: DoraDeploymentEventService | None = None,
        lead_time_service: DoraLeadTimeService | None = None,
        failure_service: DoraFailureService | None = None,
        aggregation_service: DoraAggregationService | None = None,
    ) -> None:
        self.config_service = config_service or DoraConfigService()
        self.provider_service = provider_service
        self.deployment_event_service = deployment_event_service or DoraDeploymentEventService()
        self.lead_time_service = lead_time_service or DoraLeadTimeService()
        self.failure_service = failure_service or DoraFailureService()
        self.aggregation_service = aggregation_service or DoraAggregationService()
        self.logger = LocalLogging.get_logger("hape.dora_service")

    @staticmethod
    def _split_csv(value: str) -> list[str]:
        items = [item.strip() for item in value.split(",")]
        return [item for item in items if item]

    @staticmethod
    def _build_no_data_tables(project_rows: list[dict]) -> tuple[list[dict], list[dict]]:
        no_deploy_data_rows = [row for row in project_rows if int(row["has_deployments"]) == 0]
        no_change_data_rows = [row for row in project_rows if int(row["has_change_data"]) == 0]
        return no_deploy_data_rows, no_change_data_rows

    @staticmethod
    def _resolve_provider_scopes(provider: str) -> list[str]:
        if provider == "github":
            return DoraService._split_csv(Config.get_dora_github_orgs_csv())
        return DoraService._split_csv(Config.get_dora_gitlab_group_ids_csv())

    def _resolve_provider_service(self, provider: str) -> DoraGitLabProviderService | DoraGithubProviderService:
        if self.provider_service is not None:
            return self.provider_service
        if provider == "github":
            return DoraGithubProviderService()
        return DoraGitLabProviderService()

    def _collect_project_metrics(
        self,
        project_path: str,
        project: object,
        rule: object,
        provider_service: DoraGitLabProviderService | DoraGithubProviderService,
        kubernetes_mapping: object | None,
        prometheus_url: str,
    ) -> tuple[str, list[object], tuple[float, int], list[object]]:
        deployment_events_raw = provider_service.fetch_project_deployment_jobs(project=project, rule=rule, window_days=90)
        deployment_events = self.deployment_event_service.filter_successful_deployment_events(
            events=deployment_events_raw,
            rule=rule,
        )
        if not deployment_events:
            return project_path, deployment_events, (0.0, 0), []
        commits = provider_service.fetch_project_commits(project=project, ref_name=rule.default_branch)
        lead_time = self.lead_time_service.calculate_project_lead_time_seconds(
            deployment_events=deployment_events,
            commits=commits,
        )
        failure_events = self.failure_service.evaluate_failures(
            deployment_events=deployment_events,
            project_rule=rule,
            kubernetes_mapping=kubernetes_mapping,
            prometheus_url=prometheus_url,
        )
        return project_path, deployment_events, lead_time, failure_events

    def collect_snapshot(self) -> dict:
        refresh_started_at = time.perf_counter()
        provider = Config.get_dora_provider()
        scopes = self._resolve_provider_scopes(provider=provider)
        provider_service = self._resolve_provider_service(provider=provider)
        git_rules_path = Config.get_dora_git_rules_path()
        kubernetes_mappings_path = Config.get_dora_kubernetes_mappings_path()
        prometheus_url = Config.get_dora_prometheus_url()
        project_rules, kubernetes_mappings = self.config_service.load_resolved_configuration(
            git_rules_path=git_rules_path,
            kubernetes_mappings_path=kubernetes_mappings_path,
        )
        project_rules = {project_path: rule for project_path, rule in project_rules.items() if rule.provider == provider}
        projects_by_path = provider_service.fetch_projects_for_group_ids(group_ids=scopes, project_rules=project_rules)
        deployment_events_by_project_path = {}
        lead_time_seconds_by_project_path = {}
        failure_events_by_project_path = {}
        max_workers = min(self.DEFAULT_MAX_PROJECT_WORKERS, max(1, len(projects_by_path)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_project_path = {}
            for project_path, project in projects_by_path.items():
                rule = project_rules[project_path]
                future = executor.submit(
                    self._collect_project_metrics,
                    project_path,
                    project,
                    rule,
                    provider_service,
                    kubernetes_mappings.get(project_path),
                    prometheus_url,
                )
                future_to_project_path[future] = project_path
            for future in as_completed(future_to_project_path):
                project_path, deployment_events, lead_time, failure_events = future.result()
                deployment_events_by_project_path[project_path] = deployment_events
                lead_time_seconds_by_project_path[project_path] = lead_time
                failure_events_by_project_path[project_path] = failure_events
        project_rows = self.aggregation_service.build_project_window_metrics(
            projects_by_path=projects_by_path,
            rules_by_project_path=project_rules,
            deployment_events_by_project_path=deployment_events_by_project_path,
            lead_time_seconds_by_project_path=lead_time_seconds_by_project_path,
            failure_events_by_project_path=failure_events_by_project_path,
        )
        project_rows_dicts = [item.__dict__ for item in project_rows]
        no_deploy_data_rows, no_change_data_rows = self._build_no_data_tables(project_rows=project_rows_dicts)
        refresh_elapsed_seconds = time.perf_counter() - refresh_started_at
        self.logger.info(
            "DORA snapshot collected: provider=%s projects=%s workers=%s elapsed_seconds=%.2f",
            provider,
            len(projects_by_path),
            max_workers,
            refresh_elapsed_seconds,
        )
        return {
            "projects_total": len(projects_by_path),
            "project_rows": project_rows_dicts,
            "rollups": self.aggregation_service.build_rollups(project_rows=project_rows),
            "no_deploy_data_rows": no_deploy_data_rows,
            "no_change_data_rows": no_change_data_rows,
        }


if __name__ == "__main__":
    print(DoraService)
