from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from services.confluence_service import ConfluenceService

router = APIRouter(prefix="/confluence", tags=["confluence"])


class GetPageRequest(BaseModel):
    page_id: str
    expand: str = "body.storage"


class CreatePageRequest(BaseModel):
    parent_page_id: str
    page_title: str
    page_body: str
    space_key: str
    labels: list[str] | None = None


class MdToPageRequest(BaseModel):
    parent_page_id: str | None = None
    md_path: str = "README.md"
    page_title: str | None = None
    space_key: str
    labels: list[str] | None = None


@router.post("/get-page")
def get_page(payload: GetPageRequest) -> dict:
    service = ConfluenceService()
    return service.get_page(page_id=payload.page_id, expand=payload.expand)


@router.post("/create-page")
def create_page(payload: CreatePageRequest) -> dict[str, str | dict]:
    service = ConfluenceService()
    page = service.create_page(
        parent_page_id=payload.parent_page_id,
        page_title=payload.page_title,
        page_body=payload.page_body,
        space_key=payload.space_key,
        labels=payload.labels,
    )
    page_link = service.get_page_link(page_id=page["id"], space_key=payload.space_key)
    return {"page": page, "page_link": page_link}


@router.post("/md-to-page")
def md_to_page(payload: MdToPageRequest) -> dict[str, str | dict]:
    service = ConfluenceService()
    page = service.create_page_from_markdown(
        parent_page_id=payload.parent_page_id,
        readme_path=payload.md_path,
        page_title=payload.page_title,
        space_key=payload.space_key,
        labels=payload.labels,
    )
    page_link = service.get_page_link(page_id=page["id"], space_key=payload.space_key)
    return {"page": page, "page_link": page_link}
