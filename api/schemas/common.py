from __future__ import annotations

from pydantic import BaseModel


class ApiMessage(BaseModel):
    message: str
