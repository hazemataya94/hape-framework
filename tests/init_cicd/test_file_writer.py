from pathlib import Path

import pytest

from services.init_cicd.writer.file_writer import FileWriter


def test_write_file_creates_new_file(tmp_path: Path) -> None:
    file_writer = FileWriter()
    write_result = file_writer.write_file(project_path=tmp_path, relative_path="deployments/service.yaml", content="kind: Service\n")
    assert write_result.created_files == ["deployments/service.yaml"]
    assert write_result.skipped_files == []
    assert (tmp_path / "deployments" / "service.yaml").exists()


def test_write_file_skips_existing_file(tmp_path: Path) -> None:
    target_path = tmp_path / "Dockerfile"
    target_path.write_text("FROM nginx:alpine\n", encoding="utf-8")
    file_writer = FileWriter()
    write_result = file_writer.write_file(project_path=tmp_path, relative_path="Dockerfile", content="FROM node:20\n")
    assert write_result.created_files == []
    assert write_result.skipped_files == ["Dockerfile"]
    assert target_path.read_text(encoding="utf-8") == "FROM nginx:alpine\n"


def test_write_files_aggregates_results(tmp_path: Path) -> None:
    (tmp_path / ".dockerignore").write_text("node_modules\n", encoding="utf-8")
    file_writer = FileWriter()
    write_result = file_writer.write_files(
        project_path=tmp_path,
        file_map={"Dockerfile": "FROM nginx:alpine\n", ".dockerignore": "dist\n"},
    )
    assert "Dockerfile" in write_result.created_files
    assert ".dockerignore" in write_result.skipped_files


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
