import json
from pathlib import Path

import pytest

from services.dora_config_service import DoraConfigService


def test_resolve_project_rules_with_group_and_project_overrides(tmp_path: Path) -> None:
    deployment_rules = {
        "version": 1,
        "defaults": {
            "provider": "gitlab",
            "environment": "production",
            "successful_job_statuses": ["success"],
            "deploy_job_names": ["deploy"],
            "deploy_job_name_regex": [],
            "deploy_stages": ["deploy"],
            "failure_detection_minutes": 60,
            "recovery_timeout_minutes": 240,
            "recovery_stability_minutes": 10,
        },
        "groups": [{"group_path": "example/platform", "defaults": {"deploy_job_names": ["release"]}}],
        "projects": [
            {
                "project_path": "example/platform/service-a",
                "project_id": 1,
                "default_branch": "main",
                "refs": ["main"],
                "deploy_job_names": ["deploy-prod"],
            }
        ],
    }
    git_rules_path = tmp_path / "git-rules.json"
    git_rules_path.write_text(json.dumps(deployment_rules), encoding="utf-8")
    kubernetes_mappings = {
        "version": 1,
        "defaults": {"provider": "gitlab", "cluster": "kind-hape", "workload_kind": "Deployment"},
        "projects": [
            {
                "project_path": "example/platform/service-a",
                "namespace": "payments",
                "workloads": [{"kind": "Deployment", "name": "service-a", "prometheus_label_matchers": {"deployment": "service-a"}}],
            }
        ],
    }
    kubernetes_mappings_path = tmp_path / "kubernetes-mappings.json"
    kubernetes_mappings_path.write_text(json.dumps(kubernetes_mappings), encoding="utf-8")

    service = DoraConfigService()
    project_rules, kube_mappings = service.load_resolved_configuration(
        git_rules_path=str(git_rules_path),
        kubernetes_mappings_path=str(kubernetes_mappings_path),
    )

    assert "example/platform/service-a" in project_rules
    assert project_rules["example/platform/service-a"].deploy_job_names == ["deploy-prod"]
    assert project_rules["example/platform/service-a"].refs == ["main"]
    assert kube_mappings["example/platform/service-a"].namespace == "payments"


def test_resolve_project_rules_requires_explicit_refs(tmp_path: Path) -> None:
    deployment_rules = {
        "version": 1,
        "defaults": {"provider": "gitlab"},
        "projects": [{"project_path": "example/platform/service-a", "project_id": 1}],
    }
    git_rules_path = tmp_path / "git-rules.json"
    git_rules_path.write_text(json.dumps(deployment_rules), encoding="utf-8")
    kubernetes_mappings = {
        "version": 1,
        "defaults": {"provider": "gitlab"},
        "projects": [{"project_path": "example/platform/service-a", "workloads": []}],
    }
    kubernetes_mappings_path = tmp_path / "kubernetes-mappings.json"
    kubernetes_mappings_path.write_text(json.dumps(kubernetes_mappings), encoding="utf-8")

    service = DoraConfigService()
    with pytest.raises(Exception):
        service.load_resolved_configuration(
            git_rules_path=str(git_rules_path),
            kubernetes_mappings_path=str(kubernetes_mappings_path),
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
