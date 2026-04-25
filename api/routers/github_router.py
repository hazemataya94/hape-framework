from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from services.github_service import GitHubService

router = APIRouter(prefix="/github", tags=["github"])


class InitRepoRequest(BaseModel):
    repo_path: str
    owner: str | None = None
    name: str | None = None
    visibility: str = "private"


@router.post("/init-repo")
def init_repo(payload: InitRepoRequest) -> dict[str, str]:
    service = GitHubService()
    return service.init_repo(repo_path=payload.repo_path, owner=payload.owner, name=payload.name, visibility=payload.visibility)
