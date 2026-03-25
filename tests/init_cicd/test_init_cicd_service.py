from pathlib import Path

import pytest

from core.errors import HapeValidationError
from services.init_cicd.init_cicd_service import InitCicdService


def test_init_cicd_service_project_path_not_found() -> None:
    init_cicd_service = InitCicdService()
    with pytest.raises(HapeValidationError) as exc:
        init_cicd_service.init_cicd(project_path="/tmp/path-that-does-not-exist-12345", deployment_type="kubernetes")
    assert exc.value.code == "INIT_CICD_PROJECT_PATH_NOT_FOUND"


def test_init_cicd_service_project_path_is_not_directory(tmp_path: Path) -> None:
    project_file = tmp_path / "file.txt"
    project_file.write_text("demo", encoding="utf-8")
    init_cicd_service = InitCicdService()
    with pytest.raises(HapeValidationError) as exc:
        init_cicd_service.init_cicd(project_path=str(project_file), deployment_type="kubernetes")
    assert exc.value.code == "INIT_CICD_PROJECT_PATH_NOT_DIRECTORY"


def test_init_cicd_service_deployment_type_unsupported(tmp_path: Path) -> None:
    project_dir = tmp_path / "react-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    init_cicd_service = InitCicdService()
    with pytest.raises(HapeValidationError) as exc:
        init_cicd_service.init_cicd(project_path=str(project_dir), deployment_type="aws-serverless")
    assert exc.value.code == "INIT_CICD_DEPLOYMENT_TYPE_UNSUPPORTED"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
