from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from services.markdown_service import MarkdownService

router = APIRouter(prefix="/markdown", tags=["markdown"])


class ExportTablesRequest(BaseModel):
    md_file: str
    output_dir: str
    delimiter: str = ","


class ImportCsvTableRequest(BaseModel):
    csv_file: str
    md_file: str
    delimiter: str = ","
    table_title: str | None = None


@router.post("/export-tables-to-csv")
def export_tables_to_csv(payload: ExportTablesRequest) -> dict[str, list[str]]:
    service = MarkdownService()
    files = service.export_tables_to_csv(markdown_file=payload.md_file, output_dir=payload.output_dir, delimiter=payload.delimiter)
    return {"output_files": files}


@router.post("/import-csv-table")
def import_csv_table(payload: ImportCsvTableRequest) -> dict[str, str]:
    service = MarkdownService()
    output_path = service.import_csv_table(csv_file=payload.csv_file, markdown_file=payload.md_file, delimiter=payload.delimiter, table_title=payload.table_title)
    return {"markdown_file": output_path}
