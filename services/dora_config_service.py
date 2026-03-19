from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.errors.exceptions import HapeOperationError, HapeValidationError
from core.errors.messages.dora_error_messages import get_dora_error_message
from core.logging import LocalLogging
from services.dora_models import DoraKubernetesMapping, DoraProjectRule, DoraWorkloadMapping


class DoraConfigService:
    DEFAULT_GIT_RULES = "config/dora/git-rules.json"
    DEFAULT_KUBERNETES_MAPPINGS = "config/dora/kubernetes-mappings.json"

    def __init__(self) -> None:
        self.logger = LocalLogging.get_logger("hape.dora_config_service")

    @staticmethod
    def _merge_rules(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        merged = dict(base)
        for key, value in override.items():
            if value is None:
                continue
            merged[key] = value
        return merged

    @staticmethod
    def _validate_required_keys(payload: dict[str, Any], required_keys: list[str], schema_name: str) -> None:
        for key in required_keys:
            if key not in payload:
                raise HapeValidationError(
                    code="DORA_CONFIG_INVALID_SCHEMA",
                    message=get_dora_error_message(
                        "DORA_CONFIG_INVALID_SCHEMA",
                        reason=f"{schema_name} is missing key '{key}'",
                    ),
                )

    @staticmethod
    def _load_json(path: str, config_name: str) -> dict[str, Any]:
        if not path or not path.strip():
            raise HapeValidationError(
                code="DORA_CONFIG_PATH_REQUIRED",
                message=get_dora_error_message("DORA_CONFIG_PATH_REQUIRED", config_name=config_name),
            )
        file_path = Path(path).expanduser()
        if not file_path.exists():
            raise HapeValidationError(
                code="DORA_CONFIG_NOT_FOUND",
                message=get_dora_error_message("DORA_CONFIG_NOT_FOUND", path=str(file_path)),
            )
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise HapeValidationError(
                code="DORA_CONFIG_INVALID_JSON",
                message=get_dora_error_message("DORA_CONFIG_INVALID_JSON", path=str(file_path)),
            ) from exc

    def load_git_rules(self, git_rules_path: str) -> dict[str, Any]:
        payload = self._load_json(path=git_rules_path, config_name="git rules")
        self._validate_required_keys(payload=payload, required_keys=["version", "defaults", "projects"], schema_name="git rules")
        return payload

    def load_kubernetes_mappings(self, kubernetes_mappings_path: str) -> dict[str, Any]:
        payload = self._load_json(path=kubernetes_mappings_path, config_name="kubernetes mappings")
        self._validate_required_keys(payload=payload, required_keys=["version", "defaults", "projects"], schema_name="kubernetes mappings")
        return payload

    def resolve_project_rules(self, git_rules: dict[str, Any]) -> dict[str, DoraProjectRule]:
        defaults = git_rules.get("defaults", {})
        groups = git_rules.get("groups", [])
        projects = git_rules.get("projects", [])
        group_defaults_by_path = {group.get("group_path", ""): group.get("defaults", {}) for group in groups}
        rules_by_project_path: dict[str, DoraProjectRule] = {}
        for project in projects:
            project_path = str(project.get("project_path", "")).strip()
            if not project_path:
                continue
            refs = project.get("refs", [])
            if not refs:
                raise HapeValidationError(
                    code="DORA_PROJECT_RULES_MISSING_REFS",
                    message=get_dora_error_message("DORA_PROJECT_RULES_MISSING_REFS", project_path=project_path),
                )
            group_path = "/".join(project_path.split("/")[:-1])
            merged = self._merge_rules(base=defaults, override=group_defaults_by_path.get(group_path, {}))
            merged = self._merge_rules(base=merged, override=project)
            rules_by_project_path[project_path] = DoraProjectRule(
                provider=str(merged.get("provider", "gitlab")),
                group_path=group_path,
                project_path=project_path,
                project_id=merged.get("project_id"),
                default_branch=str(merged.get("default_branch", "main")),
                refs=list(merged.get("refs", [])),
                environment=str(merged.get("environment", "production")),
                successful_job_statuses=list(merged.get("successful_job_statuses", ["success"])),
                deploy_job_names=list(merged.get("deploy_job_names", ["deploy"])),
                deploy_job_name_regex=list(merged.get("deploy_job_name_regex", [])),
                deploy_stages=list(merged.get("deploy_stages", [])),
                failure_detection_minutes=int(merged.get("failure_detection_minutes", 60)),
                recovery_timeout_minutes=int(merged.get("recovery_timeout_minutes", 240)),
                recovery_stability_minutes=int(merged.get("recovery_stability_minutes", 10)),
            )
        return rules_by_project_path

    def resolve_kubernetes_mappings(self, kubernetes_mappings: dict[str, Any]) -> dict[str, DoraKubernetesMapping]:
        defaults = kubernetes_mappings.get("defaults", {})
        projects = kubernetes_mappings.get("projects", [])
        mappings_by_project_path: dict[str, DoraKubernetesMapping] = {}
        for project in projects:
            project_path = str(project.get("project_path", "")).strip()
            if not project_path:
                continue
            merged = self._merge_rules(base=defaults, override=project)
            workloads_payload = project.get("workloads", [])
            workloads: list[DoraWorkloadMapping] = []
            for workload in workloads_payload:
                workloads.append(
                    DoraWorkloadMapping(
                        kind=str(workload.get("kind", merged.get("workload_kind", "Deployment"))),
                        name=str(workload.get("name", "")),
                        prometheus_label_matchers=dict(workload.get("prometheus_label_matchers", {})),
                    )
                )
            mappings_by_project_path[project_path] = DoraKubernetesMapping(
                provider=str(merged.get("provider", "gitlab")),
                project_path=project_path,
                cluster=str(merged.get("cluster", "kind-hape")),
                namespace=str(merged.get("namespace", "default")),
                workloads=workloads,
            )
        return mappings_by_project_path

    def load_resolved_configuration(self, git_rules_path: str, kubernetes_mappings_path: str) -> tuple[dict[str, DoraProjectRule], dict[str, DoraKubernetesMapping]]:
        try:
            git_rules = self.load_git_rules(git_rules_path=git_rules_path)
            kubernetes_mappings = self.load_kubernetes_mappings(kubernetes_mappings_path=kubernetes_mappings_path)
            project_rules = self.resolve_project_rules(git_rules=git_rules)
            kube_mappings = self.resolve_kubernetes_mappings(kubernetes_mappings=kubernetes_mappings)
            missing_projects = [project_path for project_path in kube_mappings if project_path not in project_rules]
            if missing_projects:
                raise HapeValidationError(
                    code="DORA_PROJECT_RULES_MISSING_PROJECT",
                    message=get_dora_error_message("DORA_PROJECT_RULES_MISSING_PROJECT", project_path=missing_projects[0]),
                )
            return project_rules, kube_mappings
        except HapeValidationError:
            raise
        except Exception as exc:
            raise HapeOperationError(
                code="DORA_CONFIG_INVALID_SCHEMA",
                message=get_dora_error_message("DORA_CONFIG_INVALID_SCHEMA", reason=str(exc)),
            ) from exc


if __name__ == "__main__":
    print(DoraConfigService.DEFAULT_GIT_RULES)
