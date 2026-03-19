import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from typing import Any

from core.config import Config
from core.logging import LocalLogging
from services.eks_deployment_cost_service import EksDeploymentCostService

METRICS_CATALOG = [
    {
        "name": "hape_eks_deployment_cost_exporter_up",
        "type": "gauge",
        "description": "1 when exporter refresh succeeds.",
        "labels": [],
    },
    {
        "name": "hape_eks_deployment_cost_exporter_last_refresh_timestamp_seconds",
        "type": "gauge",
        "description": "Last successful or failed refresh timestamp.",
        "labels": [],
    },
    {
        "name": "hape_eks_deployment_cost_workload_count",
        "type": "gauge",
        "description": "Count of discovered workloads.",
        "labels": [],
    },
    {
        "name": "hape_eks_deployment_cost_total_cpu_request_cores",
        "type": "gauge",
        "description": "Total CPU requests across workloads.",
        "labels": [],
    },
    {
        "name": "hape_eks_deployment_cost_total_memory_request_gib",
        "type": "gauge",
        "description": "Total memory requests across workloads.",
        "labels": [],
    },
    {
        "name": "hape_eks_deployment_cost_total_hourly_cpu_usd",
        "type": "gauge",
        "description": "Estimated hourly CPU cost.",
        "labels": [],
    },
    {
        "name": "hape_eks_deployment_cost_total_hourly_memory_usd",
        "type": "gauge",
        "description": "Estimated hourly memory cost.",
        "labels": [],
    },
    {
        "name": "hape_eks_deployment_cost_total_usd",
        "type": "gauge",
        "description": "Estimated total cost by period.",
        "labels": ["period=hourly|daily|monthly|yearly"],
    },
    {
        "name": "hape_eks_deployment_cost_workload_max_hourly_usd",
        "type": "gauge",
        "description": "Estimated workload hourly cost (max CPU or memory).",
        "labels": ["resource_type", "namespace", "name", "instance_type"],
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


class EksDeploymentCostMetricsProvider:
    DEFAULT_REFRESH_SECONDS = 300

    def __init__(
        self,
        refresh_seconds: int = DEFAULT_REFRESH_SECONDS,
        kube_context: str | None = None,
        aws_profile: str | None = None,
        ignored_namespaces_csv: str | None = None,
    ) -> None:
        self.refresh_seconds = refresh_seconds
        self.kube_context = kube_context
        self.aws_profile = aws_profile
        self.ignored_namespaces_csv = ignored_namespaces_csv
        self.service = EksDeploymentCostService()
        self.logger = LocalLogging.get_logger("hape.eks_deployment_cost_exporter")
        self._lock = Lock()
        self._last_refresh_epoch_seconds = 0.0
        self._last_metrics_payload = ""
        self._last_error = ""

    def _refresh(self) -> None:
        self.logger.debug("Refreshing exporter metrics.")
        try:
            report_file_paths = self.service.generate_report(
                kube_context=self.kube_context,
                aws_profile=self.aws_profile,
                ignored_namespaces_csv=self.ignored_namespaces_csv,
                use_incluster_config=self.kube_context is None,
            )
            summary_path = Path(report_file_paths["summary_json_path"])
            summary_report = json.loads(summary_path.read_text(encoding="utf-8"))
            self._last_metrics_payload = self._build_payload(summary_report=summary_report, exporter_up=1)
            self._last_error = ""
            self.logger.debug("Exporter metrics refreshed successfully.")
        except Exception as exc:
            self._last_error = str(exc)
            self.logger.exception("Failed to refresh EKS deployment cost metrics.")
            self._last_metrics_payload = self._build_payload(summary_report=None, exporter_up=0)
        self._last_refresh_epoch_seconds = time.time()

    def _build_payload(self, summary_report: dict[str, Any] | None, exporter_up: int) -> str:
        lines = [
            *_metric_metadata_lines("hape_eks_deployment_cost_exporter_up"),
            _metric_line("hape_eks_deployment_cost_exporter_up", exporter_up),
            *_metric_metadata_lines("hape_eks_deployment_cost_exporter_last_refresh_timestamp_seconds"),
            _metric_line("hape_eks_deployment_cost_exporter_last_refresh_timestamp_seconds", int(time.time())),
        ]
        if not summary_report:
            lines.extend(
                [
                    *_metric_metadata_lines("hape_eks_deployment_cost_workload_count"),
                    _metric_line("hape_eks_deployment_cost_workload_count", 0),
                ]
            )
            return "\n".join(lines) + "\n"

        summary = summary_report.get("summary", {})
        top_workloads = summary_report.get("top_costing_workloads", [])

        lines.extend(
            [
                *_metric_metadata_lines("hape_eks_deployment_cost_workload_count"),
                _metric_line("hape_eks_deployment_cost_workload_count", int(summary.get("workload_count", 0))),
                *_metric_metadata_lines("hape_eks_deployment_cost_total_cpu_request_cores"),
                _metric_line("hape_eks_deployment_cost_total_cpu_request_cores", float(summary.get("total_cpu_request_cores", 0.0))),
                *_metric_metadata_lines("hape_eks_deployment_cost_total_memory_request_gib"),
                _metric_line("hape_eks_deployment_cost_total_memory_request_gib", float(summary.get("total_memory_request_gib", 0.0))),
                *_metric_metadata_lines("hape_eks_deployment_cost_total_hourly_cpu_usd"),
                _metric_line("hape_eks_deployment_cost_total_hourly_cpu_usd", float(summary.get("hourly_cpu_cost_usd", 0.0))),
                *_metric_metadata_lines("hape_eks_deployment_cost_total_hourly_memory_usd"),
                _metric_line("hape_eks_deployment_cost_total_hourly_memory_usd", float(summary.get("hourly_memory_cost_usd", 0.0))),
                *_metric_metadata_lines("hape_eks_deployment_cost_total_usd"),
                _metric_line("hape_eks_deployment_cost_total_usd", float(summary.get("max_hourly_cost_usd", 0.0)), labels={"period": "hourly"}),
                _metric_line("hape_eks_deployment_cost_total_usd", float(summary.get("daily_cost_usd", 0.0)), labels={"period": "daily"}),
                _metric_line("hape_eks_deployment_cost_total_usd", float(summary.get("monthly_cost_usd", 0.0)), labels={"period": "monthly"}),
                _metric_line("hape_eks_deployment_cost_total_usd", float(summary.get("yearly_cost_usd", 0.0)), labels={"period": "yearly"}),
                *_metric_metadata_lines("hape_eks_deployment_cost_workload_max_hourly_usd"),
            ]
        )
        for workload in top_workloads:
            labels = {
                "resource_type": str(workload.get("resource_type", "")),
                "namespace": str(workload.get("namespace", "")),
                "name": str(workload.get("name", "")),
                "instance_type": str(workload.get("instance_type", "")),
            }
            lines.append(
                _metric_line(
                    "hape_eks_deployment_cost_workload_max_hourly_usd",
                    float(workload.get("max_hourly_cost_usd", 0.0)),
                    labels=labels,
                )
            )
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


def make_handler(provider: EksDeploymentCostMetricsProvider) -> type[BaseHTTPRequestHandler]:
    class EksDeploymentCostExporterHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path in ("/", "/catalog", "/metrics-catalog"):
                payload = provider.get_metrics_catalog_json().encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            if self.path == "/metrics":
                payload = provider.get_metrics_payload().encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            if self.path == "/healthz":
                error = provider.get_last_error()
                if error:
                    body = "degraded\n".encode("utf-8")
                    self.send_response(503)
                else:
                    body = "ok\n".encode("utf-8")
                    self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_response(404)
            self.end_headers()

        def log_message(self, format_text: str, *args: Any) -> None:
            provider.logger.debug(format_text, *args)

    return EksDeploymentCostExporterHandler


def main() -> None:
    LocalLogging.bootstrap()
    host = Config.get_exporter_host()
    port = Config.get_exporter_port()
    refresh_seconds = Config.get_exporter_refresh_seconds()
    kube_context = Config.get_edc_kube_context() or None
    aws_profile = Config.get_edc_aws_profile() or None
    ignored_namespaces_csv = Config.get_edc_ignored_namespaces_csv()
    provider = EksDeploymentCostMetricsProvider(
        refresh_seconds=refresh_seconds,
        kube_context=kube_context,
        aws_profile=aws_profile,
        ignored_namespaces_csv=ignored_namespaces_csv,
    )
    handler = make_handler(provider=provider)
    server = ThreadingHTTPServer((host, port), handler)
    logger = LocalLogging.get_logger("hape.eks_deployment_cost_exporter")
    logger.info("Starting EKS deployment cost exporter on %s:%s", host, port)
    server.serve_forever()


if __name__ == "__main__":
    main()
