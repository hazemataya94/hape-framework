from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from services.github_service import GitHubService

router = APIRouter(prefix="/github", tags=["github"])


class InitRepoRequest(BaseModel):
    repo_path: str
    owner: str | None = None
    name: str | None = None
    visibility: str = "private"


class ListReposRequest(BaseModel):
    org: str | None = None
    include_archived: bool = False


class DeleteReposRequest(BaseModel):
    org: str
    include: list[str] | None = None
    exclude: list[str] | None = None
    delete_all: bool = False
    confirmation_phrase: str


@router.post("/init-repo")
def init_repo(payload: InitRepoRequest) -> dict[str, str]:
    service = GitHubService()
    return service.init_repo(repo_path=payload.repo_path, owner=payload.owner, name=payload.name, visibility=payload.visibility)


@router.post("/list-repos")
def list_repos(payload: ListReposRequest) -> list[dict[str, Any]]:
    service = GitHubService()
    return service.list_repositories(org=payload.org, include_archived=payload.include_archived)


@router.post("/user-info")
def user_info() -> dict[str, str]:
    service = GitHubService()
    return service.get_authenticated_user_info()


@router.post("/delete-repos")
def delete_repos(payload: DeleteReposRequest) -> dict[str, Any]:
    service = GitHubService()
    return service.delete_repositories(
        org=payload.org,
        include=payload.include,
        exclude=payload.exclude,
        delete_all=payload.delete_all,
        confirmation_phrase=payload.confirmation_phrase,
    )
