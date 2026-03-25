from pathlib import Path

import pytest

from services.init_cicd.models import DetectedProject
from services.init_cicd.scaffolders.reactjs_scaffolder import ReactJsScaffolder


def _build_detected_project(project_path: Path, build_flavor: str = "vite", build_output_dir: str = "dist") -> DetectedProject:
    return DetectedProject(
        framework="reactjs",
        build_flavor=build_flavor,
        app_name="demo-app",
        project_path=str(project_path),
        build_output_dir=build_output_dir,
    )


def test_scaffolder_generates_all_files_for_new_project(fixture_project_factory) -> None:
    project_path = fixture_project_factory("react_vite")
    scaffolder = ReactJsScaffolder()
    result = scaffolder.scaffold(detected_project=_build_detected_project(project_path=project_path), deployment_type="kubernetes")
    assert result.deployment_type == "kubernetes"
    assert "deployments/deployment.yaml" in result.created_files
    assert "deployments/service.yaml" in result.created_files
    assert "Dockerfile" in result.created_files
    assert ".github/workflows/deploy.yaml" in result.created_files
    assert result.skipped_files == []


def test_scaffolder_skips_deployments_but_generates_root_files_when_deployments_exist(fixture_project_factory) -> None:
    project_path = fixture_project_factory("react_vite")
    (project_path / "deployments").mkdir(parents=True, exist_ok=True)
    scaffolder = ReactJsScaffolder()
    result = scaffolder.scaffold(detected_project=_build_detected_project(project_path=project_path), deployment_type="kubernetes")
    assert "deployments/deployment.yaml" not in result.created_files
    assert "Dockerfile" in result.created_files
    assert ".github/workflows/deploy.yaml" in result.created_files
    assert any("deployments/ already exists" in warning for warning in result.warnings)


def test_scaffolder_warns_when_dockerfile_and_workflow_exist(fixture_project_factory) -> None:
    project_path = fixture_project_factory("react_vite")
    (project_path / "Dockerfile").write_text("FROM nginx:alpine\n", encoding="utf-8")
    workflow_path = project_path / ".github" / "workflows"
    workflow_path.mkdir(parents=True, exist_ok=True)
    (workflow_path / "deploy.yaml").write_text("name: existing\n", encoding="utf-8")
    scaffolder = ReactJsScaffolder()
    result = scaffolder.scaffold(detected_project=_build_detected_project(project_path=project_path), deployment_type="kubernetes")
    assert "Dockerfile" in result.skipped_files
    assert ".github/workflows/deploy.yaml" in result.skipped_files
    assert any("Dockerfile already exists" in warning for warning in result.warnings)
    assert any("deploy.yaml already exists" in warning for warning in result.warnings)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
