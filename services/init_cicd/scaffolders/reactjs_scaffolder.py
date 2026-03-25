from pathlib import Path

from core.logging import LocalLogging
from services.init_cicd.models import DetectedProject, InitCicdResult
from services.init_cicd.renderer.template_renderer import TemplateRenderer
from services.init_cicd.scaffolders.base_scaffolder import BaseScaffolder
from services.init_cicd.writer.file_writer import FileWriter


class ReactJsScaffolder(BaseScaffolder):
    DEFAULT_TEMPLATE_RENDERER: TemplateRenderer | None = None
    DEFAULT_FILE_WRITER: FileWriter | None = None

    def __init__(self, template_renderer: TemplateRenderer | None = DEFAULT_TEMPLATE_RENDERER, file_writer: FileWriter | None = DEFAULT_FILE_WRITER) -> None:
        self.template_renderer = template_renderer or TemplateRenderer()
        self.file_writer = file_writer or FileWriter()
        self.logger = LocalLogging.get_logger("hape.react_js_scaffolder")

    def _build_template_context(self, detected_project: DetectedProject) -> dict[str, str]:
        return {
            "app_name": detected_project.app_name,
            "image_repository": f"docker.io/CHANGE_ME/{detected_project.app_name}",
            "image_tag": "latest",
            "container_port": "80",
            "service_port": "80",
            "replicas": "2",
            "min_replicas": "2",
            "max_replicas": "5",
            "cpu_request": "100m",
            "memory_request": "128Mi",
            "memory_limit": "512Mi",
            "build_output_dir": detected_project.build_output_dir,
            "workflow_name": "deploy",
        }

    def _build_template_map(self) -> dict[str, str]:
        return {
            "deployments/deployment.yaml": "deployment.yaml.tpl",
            "deployments/service.yaml": "service.yaml.tpl",
            "deployments/serviceaccount.yaml": "serviceaccount.yaml.tpl",
            "deployments/hpa.yaml": "hpa.yaml.tpl",
            "deployments/kustomization.yaml": "kustomization.yaml.tpl",
            "Dockerfile": "Dockerfile.tpl",
            ".dockerignore": ".dockerignore.tpl",
            ".github/workflows/deploy.yaml": "github-deploy.yaml.tpl",
        }

    def _render_templates(self, template_root: Path, context: dict[str, str], include_manifests: bool) -> dict[str, str]:
        rendered_files: dict[str, str] = {}
        for output_path, template_name in self._build_template_map().items():
            if not include_manifests and output_path.startswith("deployments/"):
                continue
            template_path = template_root / template_name
            rendered_files[output_path] = self.template_renderer.render_file(template_path=template_path, context=context)
        return rendered_files

    def _append_skip_warnings(self, result: InitCicdResult) -> None:
        if "Dockerfile" in result.skipped_files:
            result.warnings.append("Dockerfile already exists and was skipped.")
        if ".github/workflows/deploy.yaml" in result.skipped_files:
            result.warnings.append(".github/workflows/deploy.yaml already exists and was skipped.")

    def scaffold(self, detected_project: DetectedProject, deployment_type: str) -> InitCicdResult:
        self.logger.debug("scaffold(detected_project: <DetectedProject>)")
        project_path = Path(detected_project.project_path)
        result = InitCicdResult(
            project_path=detected_project.project_path,
            deployment_type=deployment_type,
            framework=detected_project.framework,
            build_flavor=detected_project.build_flavor,
        )
        deployments_path = project_path / "deployments"
        include_manifests = not deployments_path.exists()
        if not include_manifests:
            result.warnings.append("deployments/ already exists. Skipping deployment manifest generation.")
        template_root = Path(__file__).resolve().parent.parent / "templates" / "reactjs"
        context = self._build_template_context(detected_project=detected_project)
        rendered_files = self._render_templates(template_root=template_root, context=context, include_manifests=include_manifests)
        write_result = self.file_writer.write_files(project_path=project_path, file_map=rendered_files)
        result.created_files.extend(write_result.created_files)
        result.skipped_files.extend(write_result.skipped_files)
        self._append_skip_warnings(result=result)
        return result


if __name__ == "__main__":
    react_js_scaffolder = ReactJsScaffolder()
    print(react_js_scaffolder.__class__.__name__)
