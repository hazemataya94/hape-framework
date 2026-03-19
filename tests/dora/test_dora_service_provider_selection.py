import pytest

import services.dora_service as dora_service_module
from services.dora_models import DoraProjectInfo, DoraProjectRule
from services.dora_service import DoraService


class _FakeConfigService:
    def load_resolved_configuration(self, git_rules_path: str, kubernetes_mappings_path: str) -> tuple[dict, dict]:
        rules = {
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
        return rules, {}


class _FakeProviderService:
    def fetch_projects_for_group_ids(self, group_ids: list[str], project_rules: dict[str, DoraProjectRule]) -> dict[str, DoraProjectInfo]:
        return {
            "example-org/service-a": DoraProjectInfo(
                provider="github",
                group_path="example-org",
                project_path="example-org/service-a",
                project_id=21,
                default_branch="main",
                archived=False,
            )
        }

    def fetch_project_deployment_jobs(self, project: DoraProjectInfo, rule: DoraProjectRule, window_days: int) -> list:
        return []

    def fetch_project_commits(self, project: DoraProjectInfo, ref_name: str, since: str | None = None, until: str | None = None) -> list:
        return []


def test_collect_snapshot_uses_github_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dora_service_module.Config, "get_dora_provider", staticmethod(lambda: "github"))
    monkeypatch.setattr(dora_service_module.Config, "get_dora_github_orgs_csv", staticmethod(lambda: "example-org"))
    monkeypatch.setattr(dora_service_module.Config, "get_dora_git_rules_path", staticmethod(lambda: "config/dora/git-rules-github.json"))
    monkeypatch.setattr(dora_service_module.Config, "get_dora_kubernetes_mappings_path", staticmethod(lambda: "config/dora/kubernetes-mappings-github.json"))
    monkeypatch.setattr(dora_service_module.Config, "get_dora_prometheus_url", staticmethod(lambda: "http://localhost:9090"))

    service = DoraService(config_service=_FakeConfigService(), provider_service=_FakeProviderService())
    snapshot = service.collect_snapshot()
    assert snapshot["projects_total"] == 1
    assert len(snapshot["project_rows"]) == 3
    assert all(row["provider"] == "github" for row in snapshot["project_rows"])


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
