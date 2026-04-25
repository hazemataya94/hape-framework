from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from services.csv_service import CsvService

router = APIRouter(prefix="/csv", tags=["csv"])


class FromJsonRequest(BaseModel):
    json_file: str | None = None
    json_content: str | None = None
    output_file: str
    delimiter: str = ","


class ToJsonRequest(BaseModel):
    csv_file: str
    output_file: str
    delimiter: str = ","


@router.post("/from-json")
def from_json(payload: FromJsonRequest) -> dict[str, str]:
    service = CsvService()
    output_file = service.from_json(output_file=payload.output_file, json_file=payload.json_file, json_content=payload.json_content, delimiter=payload.delimiter)
    return {"output_file": output_file}


@router.post("/to-json")
def to_json(payload: ToJsonRequest) -> dict[str, str]:
    service = CsvService()
    output_file = service.to_json(csv_file=payload.csv_file, output_file=payload.output_file, delimiter=payload.delimiter)
    return {"output_file": output_file}
