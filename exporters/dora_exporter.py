import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock
from typing import Any

from core.config import Config
from core.logging import LocalLogging
from services.dora_service import DoraService

METRICS_CATALOG = [
    {
        "name": "hape_dora_exporter_up",
        "type": "gauge",
        "description": "1 when exporter refresh succeeds.",
        "labels": [],
    },
    {
        "name": "hape_dora_exporter_last_refresh_timestamp_seconds",
        "type": "gauge",
        "description": "Last successful or failed refresh timestamp.",
        "labels": [],
    },
    {
        "name": "hape_dora_projects_discovered_total",
        "type": "gauge",
        "description": "Total configured projects.",
        "labels": ["provider"],
    },
    {
        "name": "hape_dora_projects_scanned_total",
        "type": "gauge",
        "description": "Total projects scanned in refresh.",
        "labels": ["provider"],
    },
    {
        "name": "hape_dora_project_info",
        "type": "gauge",
        "description": "Project metadata for DORA aggregation.",
        "labels": ["provider", "group_path", "project_path", "default_branch", "archived"],
    },
    {
        "name": "hape_dora_project_has_deployments",
        "type": "gauge",
        "description": "1 when project has successful deployments in window.",
        "labels": ["provider", "group_path", "project_path", "environment", "window"],
    },
    {
        "name": "hape_dora_deployments_total",
        "type": "gauge",
        "description": "Successful deployment count in rolling window.",
        "labels": ["provider", "group_path", "project_path", "environment", "window"],
    },
    {
        "name": "hape_dora_deployment_frequency_per_day",
        "type": "gauge",
        "description": "Successful deployments per day in rolling window.",
        "labels": ["provider", "group_path", "project_path", "environment", "window"],
    },
    {
        "name": "hape_dora_lead_time_seconds",
        "type": "gauge",
        "description": "Median lead time in seconds for project and window.",
        "labels": ["provider", "group_path", "project_path", "environment", "window"],
    },
    {
        "name": "hape_dora_failed_deployments_total",
        "type": "gauge",
        "description": "Failed deployments in rolling window.",
        "labels": ["provider", "group_path", "project_path", "environment", "window"],
    },
    {
        "name": "hape_dora_change_fail_rate_ratio",
        "type": "gauge",
        "description": "Failed deployments divided by successful deployments.",
        "labels": ["provider", "group_path", "project_path", "environment", "window"],
    },
    {
        "name": "hape_dora_failed_deployment_recovery_time_seconds",
        "type": "gauge",
        "description": "Average failed deployment recovery time in seconds.",
        "labels": ["provider", "group_path", "project_path", "environment", "window"],
    },
    {
        "name": "hape_dora_open_failed_deployments_total",
        "type": "gauge",
        "description": "Open failed deployments in rolling window.",
        "labels": ["provider", "group_path", "project_path", "environment", "window"],
    },
]
METRICS_CATALOG_BY_NAME = {metric["name"]: metric for metric in METRICS_CATALOG}


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _metric_line(name: str, value: float | int, labels: dict[str, str] | None = None) -> str:
    if not labels:
        return f"{name} {value}"
    label_parts = [f'{key}="{_escape_label(label_value)}"' for key, label_value in labels.items()]
    return f'{name}{{{",".join(label_parts)}}} {value}'


def _metric_metadata_lines(metric_name: str) -> list[str]:
    metric = METRICS_CATALOG_BY_NAME.get(metric_name)
    if metric is None:
        raise ValueError(f"Metric metadata is missing for '{metric_name}'.")
    return [f"# HELP {metric_name} {metric['description']}", f"# TYPE {metric_name} {metric['type']}"]


class DoraMetricsProvider:
    DEFAULT_REFRESH_SECONDS = 300

    def __init__(self, refresh_seconds: int = DEFAULT_REFRESH_SECONDS) -> None:
        self.refresh_seconds = refresh_seconds
        self.service = DoraService()
        self.logger = LocalLogging.get_logger("hape.dora_exporter")
        self._lock = Lock()
        self._last_refresh_epoch_seconds = 0.0
        self._last_metrics_payload = ""
        self._last_error = ""

    @staticmethod
    def _to_labels(row: dict[str, Any]) -> dict[str, str]:
        return {
            "provider": str(row.get("provider", "")),
            "group_path": str(row.get("group_path", "")),
            "project_path": str(row.get("project_path", "")),
            "environment": str(row.get("environment", "")),
            "window": str(row.get("window", "")),
        }

    def _refresh(self) -> None:
        self.logger.debug("Refreshing DORA exporter metrics.")
        try:
            snapshot = self.service.collect_snapshot()
            self._last_metrics_payload = self._build_payload(snapshot=snapshot, exporter_up=1)
            self._last_error = ""
            self.logger.debug("DORA exporter metrics refreshed successfully.")
        except Exception as exc:
            self._last_error = str(exc)
            self.logger.exception("Failed to refresh DORA metrics.")
            self._last_metrics_payload = self._build_payload(snapshot=None, exporter_up=0)
        self._last_refresh_epoch_seconds = time.time()

    def _build_payload(self, snapshot: dict[str, Any] | None, exporter_up: int) -> str:
        lines = [
            *_metric_metadata_lines("hape_dora_exporter_up"),
            _metric_line("hape_dora_exporter_up", exporter_up),
            *_metric_metadata_lines("hape_dora_exporter_last_refresh_timestamp_seconds"),
            _metric_line("hape_dora_exporter_last_refresh_timestamp_seconds", int(time.time())),
        ]
        if not snapshot:
            lines.extend(
                [
                    *_metric_metadata_lines("hape_dora_projects_discovered_total"),
                    _metric_line("hape_dora_projects_discovered_total", 0, labels={"provider": "gitlab"}),
                    *_metric_metadata_lines("hape_dora_projects_scanned_total"),
                    _metric_line("hape_dora_projects_scanned_total", 0, labels={"provider": "gitlab"}),
                ]
            )
            return "\n".join(lines) + "\n"
        project_rows = snapshot.get("project_rows", [])
        provider = str(project_rows[0].get("provider", "gitlab")) if project_rows else "gitlab"
        lines.extend(
            [
                *_metric_metadata_lines("hape_dora_projects_discovered_total"),
                _metric_line("hape_dora_projects_discovered_total", int(snapshot.get("projects_total", 0)), labels={"provider": provider}),
                *_metric_metadata_lines("hape_dora_projects_scanned_total"),
                _metric_line("hape_dora_projects_scanned_total", int(len({row.get('project_path') for row in project_rows})), labels={"provider": provider}),
                *_metric_metadata_lines("hape_dora_project_info"),
                *_metric_metadata_lines("hape_dora_project_has_deployments"),
                *_metric_metadata_lines("hape_dora_deployments_total"),
                *_metric_metadata_lines("hape_dora_deployment_frequency_per_day"),
                *_metric_metadata_lines("hape_dora_lead_time_seconds"),
                *_metric_metadata_lines("hape_dora_failed_deployments_total"),
                *_metric_metadata_lines("hape_dora_change_fail_rate_ratio"),
                *_metric_metadata_lines("hape_dora_failed_deployment_recovery_time_seconds"),
                *_metric_metadata_lines("hape_dora_open_failed_deployments_total"),
            ]
        )
        project_info_emitted: set[str] = set()
        for row in project_rows:
            identity = str(row.get("project_path", ""))
            if identity not in project_info_emitted:
                lines.append(
                    _metric_line(
                        "hape_dora_project_info",
                        1,
                        labels={
                            "provider": str(row.get("provider", "")),
                            "group_path": str(row.get("group_path", "")),
                            "project_path": identity,
                            "default_branch": str(row.get("default_branch", "")),
                            "archived": str(row.get("archived", False)).lower(),
                        },
                    )
                )
                project_info_emitted.add(identity)
            labels = self._to_labels(row=row)
            lines.append(_metric_line("hape_dora_project_has_deployments", int(row.get("has_deployments", 0)), labels=labels))
            lines.append(_metric_line("hape_dora_deployments_total", int(row.get("deployments_total", 0)), labels=labels))
            lines.append(
                _metric_line("hape_dora_deployment_frequency_per_day", float(row.get("deployment_frequency_per_day", 0.0)), labels=labels)
            )
            lines.append(_metric_line("hape_dora_lead_time_seconds", float(row.get("lead_time_seconds", 0.0)), labels=labels))
            lines.append(_metric_line("hape_dora_failed_deployments_total", int(row.get("failed_deployments_total", 0)), labels=labels))
            lines.append(_metric_line("hape_dora_change_fail_rate_ratio", float(row.get("change_fail_rate_ratio", 0.0)), labels=labels))
            lines.append(
                _metric_line(
                    "hape_dora_failed_deployment_recovery_time_seconds",
                    float(row.get("failed_deployment_recovery_time_seconds", 0.0)),
                    labels=labels,
                )
            )
            lines.append(_metric_line("hape_dora_open_failed_deployments_total", int(row.get("open_failed_deployments_total", 0)), labels=labels))
        return "\n".join(lines) + "\n"

    def get_metrics_payload(self) -> str:
        now = time.time()
        is_stale = (now - self._last_refresh_epoch_seconds) >= self.refresh_seconds
        if is_stale or not self._last_metrics_payload:
            with self._lock:
                now_locked = time.time()
                is_stale_locked = (now_locked - self._last_refresh_epoch_seconds) >= self.refresh_seconds
                if is_stale_locked or not self._last_metrics_payload:
                    self._refresh()
        return self._last_metrics_payload

    def get_last_error(self) -> str:
        return self._last_error

    def get_metrics_catalog_json(self) -> str:
        return json.dumps({"metrics": METRICS_CATALOG}, indent=2) + "\n"


def make_handler(provider: DoraMetricsProvider) -> type[BaseHTTPRequestHandler]:
    class DoraExporterHandler(BaseHTTPRequestHandler):
        def _send_payload(self, status_code: int, content_type: str, payload: bytes) -> None:
            self.send_response(status_code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            try:
                self.wfile.write(payload)
            except (BrokenPipeError, ConnectionResetError):
                provider.logger.debug(
                    "Client disconnected before response was fully sent: path=%s remote=%s",
                    self.path,
                    self.client_address,
                )

        def do_GET(self) -> None:
            if self.path in ("/", "/catalog", "/metrics-catalog"):
                payload = provider.get_metrics_catalog_json().encode("utf-8")
                self._send_payload(
                    status_code=200,
                    content_type="application/json; charset=utf-8",
                    payload=payload,
                )
                return
            if self.path == "/metrics":
                payload = provider.get_metrics_payload().encode("utf-8")
                self._send_payload(
                    status_code=200,
                    content_type="text/plain; version=0.0.4; charset=utf-8",
                    payload=payload,
                )
                return
            if self.path == "/healthz":
                error = provider.get_last_error()
                if error:
                    body = "degraded\n".encode("utf-8")
                    status_code = 503
                else:
                    body = "ok\n".encode("utf-8")
                    status_code = 200
                self._send_payload(
                    status_code=status_code,
                    content_type="text/plain; charset=utf-8",
                    payload=body,
                )
                return
            self.send_response(404)
            self.end_headers()

        def log_message(self, format_text: str, *args: Any) -> None:
            provider.logger.debug(format_text, *args)

    return DoraExporterHandler


def main() -> None:
    LocalLogging.bootstrap()
    host = Config.get_dora_exporter_host()
    port = Config.get_dora_exporter_port()
    refresh_seconds = Config.get_dora_exporter_refresh_seconds()
    provider = DoraMetricsProvider(refresh_seconds=refresh_seconds)
    handler = make_handler(provider=provider)
    server = ThreadingHTTPServer((host, port), handler)
    logger = LocalLogging.get_logger("hape.dora_exporter")
    logger.info("Starting DORA exporter on %s:%s", host, port)
    server.serve_forever()


if __name__ == "__main__":
    main()
