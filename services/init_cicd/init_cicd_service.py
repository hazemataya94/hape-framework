from pathlib import Path

from core.errors import HapeError, HapeExternalError, HapeValidationError
from core.logging import LocalLogging
from services.init_cicd.detector.project_detector import ProjectDetector
from services.init_cicd.models import InitCicdResult
from services.init_cicd.scaffolders.reactjs_scaffolder import ReactJsScaffolder


class InitCicdService:
    SUPPORTED_DEPLOYMENT_TYPES = {"kubernetes"}
    DEFAULT_PROJECT_DETECTOR: ProjectDetector | None = None
    DEFAULT_REACT_JS_SCAFFOLDER: ReactJsScaffolder | None = None

    def __init__(self, project_detector: ProjectDetector | None = DEFAULT_PROJECT_DETECTOR, react_js_scaffolder: ReactJsScaffolder | None = DEFAULT_REACT_JS_SCAFFOLDER) -> None:
        self.project_detector = project_detector or ProjectDetector()
        self.react_js_scaffolder = react_js_scaffolder or ReactJsScaffolder()
        self.logger = LocalLogging.get_logger("hape.init_cicd_service")

    def _validate_project_path(self, project_path: str) -> Path:
        normalized_path = Path(project_path).expanduser().resolve()
        if not normalized_path.exists():
            raise HapeValidationError(
                code="INIT_CICD_PROJECT_PATH_NOT_FOUND",
                message=f"project-path does not exist: {project_path}",
                context={"project_path": str(project_path)},
            )
        if not normalized_path.is_dir():
            raise HapeValidationError(
                code="INIT_CICD_PROJECT_PATH_NOT_DIRECTORY",
                message=f"project-path is not a directory: {project_path}",
                context={"project_path": str(project_path)},
            )
        return normalized_path

    def _validate_deployment_type(self, deployment_type: str) -> str:
        normalized_deployment_type = str(deployment_type).strip().lower()
        if normalized_deployment_type not in self.SUPPORTED_DEPLOYMENT_TYPES:
            raise HapeValidationError(
                code="INIT_CICD_DEPLOYMENT_TYPE_UNSUPPORTED",
                message=f"Unsupported deployment-type: {deployment_type}. Supported values: kubernetes.",
                context={"deployment_type": normalized_deployment_type},
            )
        return normalized_deployment_type

    def init_cicd(self, project_path: str, deployment_type: str) -> InitCicdResult:
        self.logger.debug("init_cicd(project_path: <str>, deployment_type: <str>)")
        normalized_project_path = self._validate_project_path(project_path=project_path)
        normalized_deployment_type = self._validate_deployment_type(deployment_type=deployment_type)
        try:
            detected_project, warnings = self.project_detector.detect(project_path=str(normalized_project_path))
            if detected_project.framework != "reactjs":
                raise HapeValidationError(
                    code="INIT_CICD_UNSUPPORTED_FRAMEWORK",
                    message=f"Unsupported framework: {detected_project.framework}",
                    context={"framework": detected_project.framework},
                )
            result = self.react_js_scaffolder.scaffold(
                detected_project=detected_project,
                deployment_type=normalized_deployment_type,
            )
            result.warnings.extend(warnings)
            return result
        except HapeError:
            raise
        except Exception as exc:
            raise HapeExternalError(
                code="INIT_CICD_EXECUTION_FAILED",
                message="Failed to initialize CI/CD scaffolding.",
                context={"project_path": str(normalized_project_path)},
            ) from exc


if __name__ == "__main__":
    init_cicd_service = InitCicdService()
    print(init_cicd_service.__class__.__name__)
