from pathlib import Path

import pytest

from core.errors import HapeValidationError
from services.init_cicd.detector.project_detector import ProjectDetector


def test_project_detector_detects_vite_fixture(fixture_project_factory) -> None:
    project_path = fixture_project_factory("react_vite")
    project_detector = ProjectDetector()
    detected_project, warnings = project_detector.detect(project_path=str(project_path))
    assert detected_project.framework == "reactjs"
    assert detected_project.build_flavor == "vite"
    assert warnings == []


def test_project_detector_missing_package_json(tmp_path: Path) -> None:
    project_path = tmp_path / "missing-package-json"
    project_path.mkdir(parents=True, exist_ok=True)
    project_detector = ProjectDetector()
    with pytest.raises(HapeValidationError) as exc:
        project_detector.detect(project_path=str(project_path))
    assert exc.value.code == "INIT_CICD_PACKAGE_JSON_MISSING"


def test_project_detector_invalid_package_json(tmp_path: Path) -> None:
    project_path = tmp_path / "invalid-package-json"
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / "package.json").write_text("{invalid-json", encoding="utf-8")
    project_detector = ProjectDetector()
    with pytest.raises(HapeValidationError) as exc:
        project_detector.detect(project_path=str(project_path))
    assert exc.value.code == "INIT_CICD_PACKAGE_JSON_INVALID"


def test_project_detector_non_react_fixture(fixture_project_factory) -> None:
    project_path = fixture_project_factory("non_react")
    project_detector = ProjectDetector()
    with pytest.raises(HapeValidationError) as exc:
        project_detector.detect(project_path=str(project_path))
    assert exc.value.code == "INIT_CICD_REACT_DEPENDENCY_REQUIRED"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
