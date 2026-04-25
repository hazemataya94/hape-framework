from __future__ import annotations

from collections import Counter

from fastapi import APIRouter
from pydantic import BaseModel

from core.config import Config
from services.gitlab_service import GitLabService

router = APIRouter(prefix="/gitlab", tags=["gitlab"])


class CloneRequest(BaseModel):
    group_id: int | None = None
    clone_dir: str = "/Users/hazem.ataya/workspace/repos"


class MrCountPerDayRequest(BaseModel):
    created_after: str
    group_id: int | None = None
    project_id: int | None = None
    username: str | None = None


@router.post("/clone")
def clone_group_projects(payload: CloneRequest) -> dict[str, str | int]:
    service = GitLabService()
    group_id = payload.group_id or Config.get_gitlab_default_group_id()
    service.clone_group_projects(group_id, payload.clone_dir)
    return {"message": "clone started/completed", "group_id": group_id, "clone_dir": payload.clone_dir}


@router.post("/mr-count-per-day")
def mr_count_per_day(payload: MrCountPerDayRequest) -> dict[str, object]:
    service = GitLabService()
    counts: Counter[str] = service.count_merge_requests_per_day(
        created_after=payload.created_after,
        group_id=payload.group_id,
        project_id=payload.project_id,
        username=payload.username,
    )
    return {"counts": dict(counts), "total": sum(counts.values())}
