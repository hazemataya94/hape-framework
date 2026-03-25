import json
from pathlib import Path
from typing import Any

from core.errors import HapeExternalError, HapeValidationError
from core.logging import LocalLogging
from services.init_cicd.detector.reactjs_detector import ReactJsDetector
from services.init_cicd.models import DetectedProject


class ProjectDetector:
    DEFAULT_REACT_JS_DETECTOR: ReactJsDetector | None = None

    def __init__(self, react_js_detector: ReactJsDetector | None = DEFAULT_REACT_JS_DETECTOR) -> None:
        self.react_js_detector = react_js_detector or ReactJsDetector()
        self.logger = LocalLogging.get_logger("hape.project_detector")

    def _read_package_json(self, project_path: Path) -> dict[str, Any]:
        package_json_path = project_path / "package.json"
        if not package_json_path.exists():
            raise HapeValidationError(
                code="INIT_CICD_PACKAGE_JSON_MISSING",
                message="Unsupported project. package.json is missing.",
                context={"project_path": str(project_path)},
            )
        try:
            return json.loads(package_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise HapeValidationError(
                code="INIT_CICD_PACKAGE_JSON_INVALID",
                message="Invalid package.json. Could not parse JSON.",
                context={"project_path": str(project_path)},
            ) from exc
        except Exception as exc:
            raise HapeExternalError(
                code="INIT_CICD_PACKAGE_JSON_READ_FAILED",
                message="Failed to read package.json.",
                context={"project_path": str(project_path)},
            ) from exc

    def detect(self, project_path: str) -> tuple[DetectedProject, list[str]]:
        self.logger.debug("detect(project_path: <str>)")
        project_root = Path(project_path)
        package_json_data = self._read_package_json(project_path=project_root)
        return self.react_js_detector.detect(project_path=str(project_root), package_json_data=package_json_data)


if __name__ == "__main__":
    project_detector = ProjectDetector()
    print(project_detector.__class__.__name__)
