from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from services.init_cicd.init_cicd_service import InitCicdService

router = APIRouter(prefix="/init-cicd", tags=["init-cicd"])


class InitCicdRequest(BaseModel):
    project_path: str
    deployment_type: str


@router.post("")
def init_cicd(payload: InitCicdRequest) -> dict[str, object]:
    service = InitCicdService()
    result = service.init_cicd(project_path=payload.project_path, deployment_type=payload.deployment_type)
    return {
        "project_path": result.project_path,
        "deployment_type": result.deployment_type,
        "framework": result.framework,
        "build_flavor": result.build_flavor,
        "created_files": result.created_files,
        "skipped_files": result.skipped_files,
        "warnings": result.warnings,
    }
