from datetime import UTC, datetime

from services.kube_agent.investigation.evidence.evidence_models import EvidenceItem
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class PodMetricsCollector:
    def _build_restart_query(self, trigger: Trigger) -> str:
        namespace = trigger.namespace or ""
        return f'sum(rate(kube_pod_container_status_restarts_total{{namespace="{namespace}",pod="{trigger.name}"}}[5m]))'

    def collect(self, trigger: Trigger, prometheus_client) -> list[EvidenceItem]:
        if trigger.type != "pod" or not trigger.namespace:
            return []
        restart_query = self._build_restart_query(trigger=trigger)
        restart_result = prometheus_client.query(promql=restart_query)
        return [
            EvidenceItem(
                key="prometheus.pod.restarts.rate",
                source="prometheus",
                resource_ref=f"pod/{trigger.namespace}/{trigger.name}",
                value=restart_result,
                observed_at=datetime.now(UTC),
                metadata={"promql": restart_query},
            )
        ]


if __name__ == "__main__":
    print(PodMetricsCollector())
