import json

import pytest

import exporters.dora_exporter as dora_exporter_module
from exporters.dora_exporter import DoraMetricsProvider, make_handler


class _FakeDoraService:
    def collect_snapshot(self) -> dict:
        return {
            "projects_total": 1,
            "project_rows": [
                {
                    "provider": "gitlab",
                    "group_path": "example/platform",
                    "project_path": "example/platform/service-a",
                    "default_branch": "main",
                    "archived": False,
                    "environment": "production",
                    "window": "7d",
                    "has_deployments": 1,
                    "deployments_total": 3,
                    "deployment_frequency_per_day": 0.42,
                    "lead_time_seconds": 3600.0,
                    "failed_deployments_total": 1,
                    "change_fail_rate_ratio": 0.333,
                    "failed_deployment_recovery_time_seconds": 1200.0,
                    "open_failed_deployments_total": 0,
                }
            ],
            "rollups": {},
            "no_deploy_data_rows": [],
            "no_change_data_rows": [],
        }


def test_metrics_payload_contains_required_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dora_exporter_module, "DoraService", _FakeDoraService)
    provider = DoraMetricsProvider(refresh_seconds=9999)
    payload = provider.get_metrics_payload()
    assert "hape_dora_exporter_up 1" in payload
    assert "hape_dora_deployments_total" in payload
    assert "hape_dora_change_fail_rate_ratio" in payload
    assert "hape_dora_failed_deployment_recovery_time_seconds" in payload


def test_metrics_catalog_is_valid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dora_exporter_module, "DoraService", _FakeDoraService)
    provider = DoraMetricsProvider(refresh_seconds=9999)
    catalog = provider.get_metrics_catalog_json()
    payload = json.loads(catalog)
    assert "metrics" in payload
    assert any(item["name"] == "hape_dora_deployments_total" for item in payload["metrics"])


def test_handler_health_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dora_exporter_module, "DoraService", _FakeDoraService)
    provider = DoraMetricsProvider(refresh_seconds=9999)
    handler_class = make_handler(provider=provider)
    assert handler_class is not None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
