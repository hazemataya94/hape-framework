from datetime import UTC, datetime

from services.kube_agent.config.kube_agent_config import KubeAgentConfig
from services.kube_agent.config.promql_queries import ALERT_STATUS
from services.kube_agent.config.promql_queries import COST_EXPORTER_UP
from services.kube_agent.config.promql_queries import COST_TOP_WORKLOADS_HOURLY
from services.kube_agent.config.promql_queries import COST_TOP_WORKLOADS_HOURLY_OFFSET
from services.kube_agent.config.promql_queries import COST_TOTAL_HOURLY
from services.kube_agent.config.promql_queries import COST_TOTAL_HOURLY_OFFSET
from services.kube_agent.config.promql_queries import COST_WORKLOAD_HOURLY
from services.kube_agent.config.promql_queries import NODE_CONDITIONS
from services.kube_agent.investigation.evidence.collectors.pod_metrics_collector import PodMetricsCollector
from services.kube_agent.investigation.evidence.evidence_models import EvidenceItem
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class PrometheusEvidenceCollector:
    def __init__(self, config: KubeAgentConfig | None = None) -> None:
        self.config = config or KubeAgentConfig.load()
        self.pod_metrics_collector = PodMetricsCollector()

    @staticmethod
    def _extract_vector_samples(result: dict) -> list[dict]:
        if not isinstance(result, dict):
            return []
        data = result.get("data")
        if not isinstance(data, dict):
            return []
        raw_samples = data.get("result")
        if not isinstance(raw_samples, list):
            return []
        normalized_samples: list[dict] = []
        for sample in raw_samples:
            if not isinstance(sample, dict):
                continue
            value = sample.get("value")
            if not isinstance(value, list) or len(value) < 2:
                continue
            try:
                normalized_value = float(value[1])
            except (TypeError, ValueError):
                continue
            normalized_samples.append({"metric": sample.get("metric") if isinstance(sample.get("metric"), dict) else {}, "value": normalized_value, "timestamp": value[0]})
        return normalized_samples

    def _collect_pod_evidence(self, trigger: Trigger, prometheus_client) -> list[EvidenceItem]:
        return self.pod_metrics_collector.collect(trigger=trigger, prometheus_client=prometheus_client)

    def _collect_node_evidence(self, trigger: Trigger, prometheus_client) -> list[EvidenceItem]:
        query = NODE_CONDITIONS.format(node=trigger.name)
        result = prometheus_client.query(promql=query)
        return [EvidenceItem(key="prometheus.node.conditions", source="prometheus", resource_ref=f"node/{trigger.name}", value=result, observed_at=datetime.now(UTC), metadata={"promql": query})]

    def _collect_alert_evidence(self, trigger: Trigger, prometheus_client) -> list[EvidenceItem]:
        query = ALERT_STATUS.format(alertname=trigger.name)
        result = prometheus_client.query(promql=query)
        return [EvidenceItem(key="prometheus.alerts", source="prometheus", resource_ref=f"alert/{trigger.name}", value=result, observed_at=datetime.now(UTC), metadata={"promql": query})]

    def _collect_cost_evidence(self, trigger: Trigger, prometheus_client) -> list[EvidenceItem]:
        if not trigger.namespace:
            return []
        historical_offset = str(trigger.metadata.get("historical_offset", "1h")).strip() or "1h"
        exporter_up_query = COST_EXPORTER_UP
        total_hourly_query = COST_TOTAL_HOURLY
        total_hourly_offset_query = COST_TOTAL_HOURLY_OFFSET.format(historical_offset=historical_offset)
        analyze_all_workloads = bool(trigger.metadata.get("all_workloads"))
        workload_hourly_query = COST_WORKLOAD_HOURLY.format(namespace=trigger.namespace, deployment=trigger.name)
        top_workloads_query = COST_TOP_WORKLOADS_HOURLY.format(top_limit=self.config.cost_top_workloads_limit)
        top_workloads_offset_query = COST_TOP_WORKLOADS_HOURLY_OFFSET.format(top_limit=self.config.cost_top_workloads_limit, historical_offset=historical_offset)

        exporter_up_result = prometheus_client.query(promql=exporter_up_query)
        total_hourly_result = prometheus_client.query(promql=total_hourly_query)
        total_hourly_offset_result = prometheus_client.query(promql=total_hourly_offset_query)
        workload_hourly_result = {"status": "success", "data": {"resultType": "vector", "result": []}}
        if not analyze_all_workloads:
            workload_hourly_result = prometheus_client.query(promql=workload_hourly_query)
        top_workloads_result = prometheus_client.query(promql=top_workloads_query)
        top_workloads_offset_result = prometheus_client.query(promql=top_workloads_offset_query)

        return [
            EvidenceItem(
                key="prometheus.cost.exporter_up",
                source="prometheus",
                resource_ref="exporter/eks-deployment-cost",
                value=self._extract_vector_samples(result=exporter_up_result),
                observed_at=datetime.now(UTC),
                metadata={"promql": exporter_up_query},
            ),
            EvidenceItem(
                key="prometheus.cost.total_hourly_usd",
                source="prometheus",
                resource_ref=f"namespace/{trigger.namespace}",
                value=self._extract_vector_samples(result=total_hourly_result),
                observed_at=datetime.now(UTC),
                metadata={"promql": total_hourly_query},
            ),
            EvidenceItem(
                key="prometheus.cost.total_hourly_usd.offset",
                source="prometheus",
                resource_ref=f"namespace/{trigger.namespace}",
                value=self._extract_vector_samples(result=total_hourly_offset_result),
                observed_at=datetime.now(UTC),
                metadata={"promql": total_hourly_offset_query, "historical_offset": historical_offset},
            ),
            EvidenceItem(
                key="prometheus.cost.workload_hourly_usd",
                source="prometheus",
                resource_ref=f"deployment/{trigger.namespace}/{trigger.name}" if not analyze_all_workloads else f"namespace/{trigger.namespace}",
                value=self._extract_vector_samples(result=workload_hourly_result),
                observed_at=datetime.now(UTC),
                metadata={"promql": workload_hourly_query, "all_workloads": analyze_all_workloads},
            ),
            EvidenceItem(
                key="prometheus.cost.top_workloads_hourly_usd",
                source="prometheus",
                resource_ref=f"namespace/{trigger.namespace}",
                value=self._extract_vector_samples(result=top_workloads_result),
                observed_at=datetime.now(UTC),
                metadata={"promql": top_workloads_query, "top_limit": self.config.cost_top_workloads_limit},
            ),
            EvidenceItem(
                key="prometheus.cost.top_workloads_hourly_usd.offset",
                source="prometheus",
                resource_ref=f"namespace/{trigger.namespace}",
                value=self._extract_vector_samples(result=top_workloads_offset_result),
                observed_at=datetime.now(UTC),
                metadata={"promql": top_workloads_offset_query, "top_limit": self.config.cost_top_workloads_limit, "historical_offset": historical_offset},
            ),
        ]

    def collect(self, trigger: Trigger, prometheus_client) -> list[EvidenceItem]:
        if trigger.type == "pod":
            return self._collect_pod_evidence(trigger=trigger, prometheus_client=prometheus_client)
        if trigger.type == "node":
            return self._collect_node_evidence(trigger=trigger, prometheus_client=prometheus_client)
        if trigger.type == "alert":
            return self._collect_alert_evidence(trigger=trigger, prometheus_client=prometheus_client)
        if trigger.type == "cost":
            return self._collect_cost_evidence(trigger=trigger, prometheus_client=prometheus_client)
        return []


if __name__ == "__main__":
    print(PrometheusEvidenceCollector())
