import re
from typing import Any

from core.errors import HapeValidationError
from core.logging import LocalLogging
from services.init_cicd.models import DetectedProject


class ReactJsDetector:
    VITE_BUILD_FLAVOR = "vite"
    CRA_BUILD_FLAVOR = "cra"
    GENERIC_BUILD_FLAVOR = "generic"
    REACT_FRAMEWORK = "reactjs"

    def __init__(self) -> None:
        self.logger = LocalLogging.get_logger("hape.react_js_detector")

    def _contains_dependency(self, package_json_data: dict[str, Any], dependency_name: str) -> bool:
        dependencies = package_json_data.get("dependencies", {})
        dev_dependencies = package_json_data.get("devDependencies", {})
        dependency_present = dependency_name in dependencies or dependency_name in dev_dependencies
        return bool(dependency_present)

    def _detect_build_flavor(self, package_json_data: dict[str, Any]) -> tuple[str, str, list[str]]:
        warnings: list[str] = []
        if self._contains_dependency(package_json_data=package_json_data, dependency_name="vite"):
            return self.VITE_BUILD_FLAVOR, "dist", warnings
        if self._contains_dependency(package_json_data=package_json_data, dependency_name="react-scripts"):
            return self.CRA_BUILD_FLAVOR, "build", warnings
        scripts = package_json_data.get("scripts", {})
        if isinstance(scripts, dict) and scripts.get("build"):
            warnings.append("Generic React project detected. Adjust Dockerfile build output directory if needed.")
            return self.GENERIC_BUILD_FLAVOR, "build", warnings
        raise HapeValidationError(
            code="INIT_CICD_REACT_BUILD_SCRIPT_REQUIRED",
            message="Unsupported React project. Expected Vite, CRA, or scripts.build.",
            context={"detector": "ReactJsDetector"},
        )

    def _normalize_app_name(self, raw_name: Any) -> str:
        app_name = str(raw_name or "").strip().lower()
        app_name = re.sub(r"[^a-z0-9-]+", "-", app_name)
        app_name = re.sub(r"-+", "-", app_name).strip("-")
        if not app_name:
            raise HapeValidationError(
                code="INIT_CICD_APP_NAME_INVALID",
                message="package.json name must normalize to a non-empty Kubernetes-safe name.",
                context={"detector": "ReactJsDetector"},
            )
        return app_name

    def detect(self, project_path: str, package_json_data: dict[str, Any]) -> tuple[DetectedProject, list[str]]:
        self.logger.debug("detect(project_path: <str>, package_json_data: <dict>)")
        if not self._contains_dependency(package_json_data=package_json_data, dependency_name="react"):
            raise HapeValidationError(
                code="INIT_CICD_REACT_DEPENDENCY_REQUIRED",
                message="Unsupported project type. Missing dependency: react.",
                context={"detector": "ReactJsDetector"},
            )
        if not self._contains_dependency(package_json_data=package_json_data, dependency_name="react-dom"):
            raise HapeValidationError(
                code="INIT_CICD_REACT_DOM_DEPENDENCY_REQUIRED",
                message="Unsupported project type. Missing dependency: react-dom.",
                context={"detector": "ReactJsDetector"},
            )
        build_flavor, build_output_dir, warnings = self._detect_build_flavor(package_json_data=package_json_data)
        app_name = self._normalize_app_name(raw_name=package_json_data.get("name"))
        detected_project = DetectedProject(
            framework=self.REACT_FRAMEWORK,
            build_flavor=build_flavor,
            app_name=app_name,
            project_path=project_path,
            build_output_dir=build_output_dir,
        )
        return detected_project, warnings


if __name__ == "__main__":
    react_js_detector = ReactJsDetector()
    sample_package = {"name": "my-app", "dependencies": {"react": "^19.0.0", "react-dom": "^19.0.0", "vite": "^5.0.0"}}
    print(react_js_detector.detect(project_path="/path/to/project", package_json_data=sample_package)[0].build_flavor)
