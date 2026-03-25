from __future__ import annotations

from urllib.parse import urlencode

from services.kube_agent.investigation.evidence.evidence_models import EvidenceItem
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class GrafanaDefaultDashboardsCollector:
    DEFAULT_DASHBOARD_RULES = [
        {
            "label": "Kubernetes Pod Resources",
            "title_tokens": ["kubernetes", "compute resources", "pod"],
            "trigger_types": {"pod", "alert"},
            "context_keys": ["namespace", "pod"],
            "signal_tokens": [],
        },
        {
            "label": "Kubernetes Namespace Pods",
            "title_tokens": ["kubernetes", "compute resources", "namespace", "pods"],
            "trigger_types": {"pod", "deployment", "alert"},
            "context_keys": ["namespace"],
            "signal_tokens": [],
        },
        {
            "label": "Kubernetes Pod Networking",
            "title_tokens": ["kubernetes", "networking", "pod"],
            "trigger_types": {"pod", "alert"},
            "context_keys": ["namespace", "pod"],
            "signal_tokens": [],
        },
        {
            "label": "Kubernetes Node Resources",
            "title_tokens": ["kubernetes", "compute resources", "node", "pods"],
            "trigger_types": {"node", "pod", "alert"},
            "context_keys": ["node"],
            "signal_tokens": ["failedscheduling", "memorypressure", "notready", "taint"],
        },
        {
            "label": "Node Exporter Nodes",
            "title_tokens": ["node exporter", "nodes"],
            "trigger_types": {"node", "pod", "alert"},
            "context_keys": ["node"],
            "signal_tokens": ["failedscheduling", "memorypressure", "diskpressure", "pidpressure", "notready", "taint"],
        },
        {
            "label": "Kubernetes Pods Overview",
            "title_tokens": ["kubernetes", "views", "pods"],
            "trigger_types": {"pod", "deployment", "alert"},
            "context_keys": ["namespace", "pod"],
            "signal_tokens": [],
        },
        {
            "label": "Kubernetes Nodes Overview",
            "title_tokens": ["kubernetes", "views", "nodes"],
            "trigger_types": {"node", "pod", "alert"},
            "context_keys": ["node"],
            "signal_tokens": ["failedscheduling", "memorypressure", "diskpressure", "pidpressure", "notready", "taint"],
        },
    ]

    @staticmethod
    def _build_context(trigger: Trigger) -> dict[str, str | None]:
        namespace = trigger.namespace or trigger.labels.get("namespace")
        pod_name = trigger.name if trigger.type == "pod" else trigger.labels.get("pod")
        deployment_name = trigger.name if trigger.type == "deployment" else trigger.labels.get("deployment")
        node_name = trigger.name if trigger.type == "node" else trigger.labels.get("node")
        return {
            "namespace": namespace,
            "pod": pod_name,
            "deployment": deployment_name,
            "node": node_name,
        }

    @staticmethod
    def _build_signal_text(evidence_items: list[EvidenceItem]) -> str:
        signal_fragments = [str(item.value).lower() for item in evidence_items if item.key in {"kubernetes.pod.events", "kubernetes.node.conditions", "kubernetes.pod.scheduling_failures"}]
        return " ".join(signal_fragments)

    @staticmethod
    def _rule_applies(rule: dict, trigger: Trigger, signal_text: str) -> bool:
        if trigger.type not in rule["trigger_types"]:
            return False
        signal_tokens = rule["signal_tokens"]
        if not signal_tokens:
            return True
        return any(token in signal_text for token in signal_tokens)

    @staticmethod
    def _find_dashboard(dashboards: list[dict], title_tokens: list[str]) -> dict | None:
        for dashboard in dashboards:
            title = str(dashboard.get("title", "")).lower()
            if all(token in title for token in title_tokens):
                return dashboard
        return None

    @staticmethod
    def _build_dashboard_url(base_url: str, dashboard_url: str, context: dict[str, str | None], context_keys: list[str]) -> str:
        query_params: list[tuple[str, str]] = []
        for context_key in context_keys:
            context_value = context.get(context_key)
            if not context_value:
                continue
            query_params.append((f"var-{context_key}", context_value))
        if not query_params:
            return f"{base_url}{dashboard_url}"
        return f"{base_url}{dashboard_url}?{urlencode(query_params)}"

    def collect(self, trigger: Trigger, evidence_items: list[EvidenceItem], grafana_client) -> dict[str, str]:
        dashboards = grafana_client.list_dashboards()
        context = self._build_context(trigger=trigger)
        signal_text = self._build_signal_text(evidence_items=evidence_items)
        links: dict[str, str] = {}
        for rule in self.DEFAULT_DASHBOARD_RULES:
            if not self._rule_applies(rule=rule, trigger=trigger, signal_text=signal_text):
                continue
            dashboard = self._find_dashboard(dashboards=dashboards, title_tokens=rule["title_tokens"])
            if not dashboard:
                continue
            dashboard_url = dashboard.get("url")
            if not dashboard_url:
                continue
            links[rule["label"]] = self._build_dashboard_url(
                base_url=grafana_client.base_url,
                dashboard_url=dashboard_url,
                context=context,
                context_keys=rule["context_keys"],
            )
        return links


if __name__ == "__main__":
    print(GrafanaDefaultDashboardsCollector())
