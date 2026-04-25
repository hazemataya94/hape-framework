from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from services.dora_config_service import DoraConfigService
from services.dora_service import DoraService

router = APIRouter(prefix="/dora", tags=["dora"])


class ValidateConfigRequest(BaseModel):
    git_rules_path: str = "config/dora/git-rules.json"
    kubernetes_mappings_path: str = "config/dora/kubernetes-mappings.json"


class ProjectPathRequest(BaseModel):
    project_path: str


@router.post("/validate-config")
def validate_config(payload: ValidateConfigRequest) -> dict[str, int]:
    service = DoraConfigService()
    project_rules, kube_mappings = service.load_resolved_configuration(git_rules_path=payload.git_rules_path, kubernetes_mappings_path=payload.kubernetes_mappings_path)
    return {"projects_count": len(project_rules), "kubernetes_mappings_count": len(kube_mappings)}


@router.post("/list-projects")
def list_projects() -> dict[str, object]:
    dora_service = DoraService()
    snapshot = dora_service.collect_snapshot()
    rows = snapshot.get("project_rows", [])
    unique_projects = sorted({row.get("project_path", "") for row in rows})
    return {"projects": unique_projects, "total": len(unique_projects)}


@router.post("/list-deployments")
def list_deployments(payload: ProjectPathRequest) -> dict[str, object]:
    dora_service = DoraService()
    snapshot = dora_service.collect_snapshot()
    rows = [row for row in snapshot.get("project_rows", []) if row.get("project_path") == payload.project_path]
    return {"rows": rows}


@router.post("/compute-project")
def compute_project(payload: ProjectPathRequest) -> dict[str, object]:
    dora_service = DoraService()
    snapshot = dora_service.collect_snapshot()
    rows = [row for row in snapshot.get("project_rows", []) if row.get("project_path") == payload.project_path]
    return {"rows": rows}
