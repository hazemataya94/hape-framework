import json
import shutil
from pathlib import Path

import pytest

from services.init_cicd.init_cicd_service import InitCicdService
from utils.test_artifacts_utils import print_artifacts_directory


TESTS_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PROJECT = Path(__file__).resolve().parent / "fixtures" / "react_vite"


def _write_result_artifacts(output_dir: Path, result) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_lines = [
        "Init CI/CD",
        f"Project: {result.project_path}",
        f"Deployment type: {result.deployment_type}",
        f"Framework: {result.framework}",
        f"Build flavor: {result.build_flavor}",
        f"Created: {result.created_files}",
        f"Skipped: {result.skipped_files}",
        f"Warnings: {result.warnings}",
    ]
    (output_dir / "init-cicd-summary.txt").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    (output_dir / "init-cicd-result.json").write_text(
        json.dumps(
            {
                "project_path": result.project_path,
                "framework": result.framework,
                "build_flavor": result.build_flavor,
                "created_files": result.created_files,
                "skipped_files": result.skipped_files,
                "warnings": result.warnings,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_init_cicd_functional_on_kind_cluster(functional_kind_cluster: dict[str, str | None], tmp_path: Path) -> None:
    assert str(functional_kind_cluster["kube_context"]).startswith("kind-")
    project_path = tmp_path / "react_vite"
    shutil.copytree(FIXTURE_PROJECT, project_path)
    init_cicd_service = InitCicdService()
    result = init_cicd_service.init_cicd(project_path=str(project_path), deployment_type="kubernetes")
    expected_files = [
        "deployments/deployment.yaml",
        "deployments/service.yaml",
        "deployments/serviceaccount.yaml",
        "deployments/hpa.yaml",
        "deployments/kustomization.yaml",
        "Dockerfile",
        ".dockerignore",
        ".github/workflows/deploy.yaml",
    ]
    for relative_path in expected_files:
        assert (project_path / relative_path).exists(), f"Missing generated file: {relative_path}"
    deployment_text = (project_path / "deployments" / "deployment.yaml").read_text(encoding="utf-8")
    assert "namespace:" not in deployment_text
    assert "cpu:" in deployment_text
    assert "limits:" in deployment_text
    limits_block = deployment_text.split("limits:", maxsplit=1)[1]
    assert "cpu:" not in limits_block
    artifacts_dir = tmp_path / "init-cicd-functional-artifacts"
    _write_result_artifacts(output_dir=artifacts_dir, result=result)
    assert (artifacts_dir / "init-cicd-summary.txt").exists()
    assert (artifacts_dir / "init-cicd-result.json").exists()
    print_artifacts_directory(artifacts_directory=artifacts_dir)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
