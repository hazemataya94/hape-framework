from datetime import UTC, datetime

from services.kube_agent.investigation.evidence.evidence_models import EvidenceItem
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class PodLogsCollector:
    DEFAULT_TAIL_LINES = 200

    def collect(self, trigger: Trigger, kubernetes_client, tail_lines: int = DEFAULT_TAIL_LINES) -> list[EvidenceItem]:
        if trigger.type != "pod" or not trigger.namespace:
            return []
        logs = kubernetes_client.get_pod_logs(namespace=trigger.namespace, pod_name=trigger.name, tail_lines=tail_lines)
        return [
            EvidenceItem(
                key="kubernetes.pod.logs",
                source="kubernetes",
                resource_ref=f"pod/{trigger.namespace}/{trigger.name}",
                value=logs,
                observed_at=datetime.now(UTC),
                metadata={"tail_lines": tail_lines},
            )
        ]


if __name__ == "__main__":
    print(PodLogsCollector())
