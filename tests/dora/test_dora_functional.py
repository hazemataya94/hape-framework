import csv
import json
from pathlib import Path

import pytest

from utils.test_artifacts_utils import print_artifacts_directory


class _FakeDoraService:
    def collect_snapshot(self) -> dict:
        return {
            "projects_total": 2,
            "project_rows": [
                {
                    "provider": "github",
                    "group_path": "hape-demos",
                    "project_path": "hape-demos/hape-dora-demo-service-a",
                    "default_branch": "main",
                    "archived": False,
                    "environment": "production",
                    "window": "7d",
                    "has_deployments": 1,
                    "deployments_total": 3,
                    "deployment_frequency_per_day": 0.42,
                    "lead_time_seconds": 3600.0,
                    "has_change_data": 1,
                    "failed_deployments_total": 1,
                    "change_fail_rate_ratio": 0.333,
                    "failed_deployment_recovery_time_seconds": 1200.0,
                    "open_failed_deployments_total": 0,
                },
                {
                    "provider": "github",
                    "group_path": "hape-demos",
                    "project_path": "hape-demos/hape-dora-demo-service-b",
                    "default_branch": "main",
                    "archived": False,
                    "environment": "production",
                    "window": "7d",
                    "has_deployments": 0,
                    "deployments_total": 0,
                    "deployment_frequency_per_day": 0.0,
                    "lead_time_seconds": 0.0,
                    "has_change_data": 0,
                    "failed_deployments_total": 0,
                    "change_fail_rate_ratio": 0.0,
                    "failed_deployment_recovery_time_seconds": 0.0,
                    "open_failed_deployments_total": 0,
                },
            ],
            "rollups": {},
            "no_deploy_data_rows": [{"project_path": "hape-demos/hape-dora-demo-service-b"}],
            "no_change_data_rows": [{"project_path": "hape-demos/hape-dora-demo-service-b"}],
        }


def test_dora_functional_artifact_generation(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    artifacts_directory = tmp_path / "dora-functional-artifacts"
    artifacts_directory.mkdir(parents=True, exist_ok=True)
    service = _FakeDoraService()
    snapshot = service.collect_snapshot()

    summary_json_path = artifacts_directory / "dora-summary.json"
    summary_json_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    project_rows_csv_path = artifacts_directory / "dora-project-rows.csv"
    with open(project_rows_csv_path, "w", encoding="utf-8", newline="") as csv_file:
        fieldnames = sorted(snapshot["project_rows"][0].keys())
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in snapshot["project_rows"]:
            writer.writerow(row)

    report_markdown_path = artifacts_directory / "dora-report.md"
    report_markdown_path.write_text(
        "# DORA Functional Report\n\n"
        f"- Projects total: {snapshot['projects_total']}\n"
        f"- No deploy data projects: {len(snapshot['no_deploy_data_rows'])}\n"
        f"- No change data projects: {len(snapshot['no_change_data_rows'])}\n",
        encoding="utf-8",
    )

    assert summary_json_path.exists()
    assert project_rows_csv_path.exists()
    assert report_markdown_path.exists()
    with capsys.disabled():
        print_artifacts_directory(artifacts_directory=artifacts_directory)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
