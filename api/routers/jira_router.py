from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from services.jira_service import JiraService

router = APIRouter(prefix="/jira", tags=["jira"])


class MdToCommentRequest(BaseModel):
    issue_key: str
    md_path: str


@router.post("/md-to-comment")
def md_to_comment(payload: MdToCommentRequest) -> dict[str, object]:
    service = JiraService()
    comment = service.add_comment_from_markdown(issue_key=payload.issue_key, markdown_path=payload.md_path)
    issue_url = service.get_issue_url(payload.issue_key)
    return {"issue_url": issue_url, "comment": comment}
