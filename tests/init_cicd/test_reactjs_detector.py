import pytest

from core.errors import HapeValidationError
from services.init_cicd.detector.reactjs_detector import ReactJsDetector


def test_detect_vite_react_project() -> None:
    detector = ReactJsDetector()
    package_json_data = {
        "name": "my-vite-app",
        "dependencies": {"react": "^19.0.0", "react-dom": "^19.0.0"},
        "devDependencies": {"vite": "^5.0.0"},
        "scripts": {"build": "vite build"},
    }
    detected_project, warnings = detector.detect(project_path="/tmp/project", package_json_data=package_json_data)
    assert detected_project.build_flavor == "vite"
    assert detected_project.build_output_dir == "dist"
    assert warnings == []


def test_detect_cra_react_project() -> None:
    detector = ReactJsDetector()
    package_json_data = {
        "name": "my-cra-app",
        "dependencies": {"react": "^19.0.0", "react-dom": "^19.0.0", "react-scripts": "^5.0.1"},
    }
    detected_project, warnings = detector.detect(project_path="/tmp/project", package_json_data=package_json_data)
    assert detected_project.build_flavor == "cra"
    assert detected_project.build_output_dir == "build"
    assert warnings == []


def test_detect_generic_react_project_warns() -> None:
    detector = ReactJsDetector()
    package_json_data = {
        "name": "my-generic-app",
        "dependencies": {"react": "^19.0.0", "react-dom": "^19.0.0"},
        "scripts": {"build": "npm run custom-build"},
    }
    detected_project, warnings = detector.detect(project_path="/tmp/project", package_json_data=package_json_data)
    assert detected_project.build_flavor == "generic"
    assert detected_project.build_output_dir == "build"
    assert warnings


def test_detect_non_react_project_fails() -> None:
    detector = ReactJsDetector()
    package_json_data = {"name": "not-react", "dependencies": {"lodash": "^4.0.0"}}
    with pytest.raises(HapeValidationError) as exc:
        detector.detect(project_path="/tmp/project", package_json_data=package_json_data)
    assert exc.value.code == "INIT_CICD_REACT_DEPENDENCY_REQUIRED"


def test_normalized_name_cannot_be_empty() -> None:
    detector = ReactJsDetector()
    package_json_data = {"name": "---", "dependencies": {"react": "^19.0.0", "react-dom": "^19.0.0"}, "scripts": {"build": "echo build"}}
    with pytest.raises(HapeValidationError) as exc:
        detector.detect(project_path="/tmp/project", package_json_data=package_json_data)
    assert exc.value.code == "INIT_CICD_APP_NAME_INVALID"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
