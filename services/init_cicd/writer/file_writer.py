from pathlib import Path

from core.errors import HapeExternalError
from core.logging import LocalLogging
from services.init_cicd.models import FileWriteResult


class FileWriter:
    def __init__(self) -> None:
        self.logger = LocalLogging.get_logger("hape.file_writer")

    def _to_relative_path(self, absolute_path: Path, project_path: Path) -> str:
        return absolute_path.relative_to(project_path).as_posix()

    def write_file(self, project_path: Path, relative_path: str, content: str) -> FileWriteResult:
        self.logger.debug("write_file(project_path: <path>, relative_path: <str>)")
        target_path = project_path / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists():
            return FileWriteResult(created_files=[], skipped_files=[self._to_relative_path(target_path, project_path)])
        try:
            target_path.write_text(content, encoding="utf-8")
            return FileWriteResult(created_files=[self._to_relative_path(target_path, project_path)], skipped_files=[])
        except Exception as exc:
            raise HapeExternalError(
                code="INIT_CICD_FILE_WRITE_FAILED",
                message=f"Failed to write file: {relative_path}",
                context={"relative_path": relative_path},
            ) from exc

    def write_files(self, project_path: Path, file_map: dict[str, str]) -> FileWriteResult:
        self.logger.debug("write_files(project_path: <path>, file_map: <dict>)")
        aggregate_result = FileWriteResult()
        for relative_path, content in file_map.items():
            write_result = self.write_file(project_path=project_path, relative_path=relative_path, content=content)
            aggregate_result.created_files.extend(write_result.created_files)
            aggregate_result.skipped_files.extend(write_result.skipped_files)
        return aggregate_result


if __name__ == "__main__":
    file_writer = FileWriter()
    print(file_writer.__class__.__name__)
