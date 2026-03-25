from datetime import UTC, datetime

from services.kube_agent.investigation.evidence.evidence_models import EvidenceItem
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class PodStatusCollector:
    def collect(self, trigger: Trigger, kubernetes_client) -> list[EvidenceItem]:
        if trigger.type != "pod" or not trigger.namespace:
            return []
        pod = kubernetes_client.get_pod(namespace=trigger.namespace, pod_name=trigger.name)
        status = pod.status
        phase = status.phase if status and status.phase else "unknown"
        conditions = []
        for condition in status.conditions or []:
            conditions.append({"type": condition.type, "status": condition.status, "reason": condition.reason, "message": condition.message})
        restart_count = 0
        for container_status in status.container_statuses or []:
            restart_count += int(container_status.restart_count or 0)
        return [
            EvidenceItem(
                key="kubernetes.pod.status",
                source="kubernetes",
                resource_ref=f"pod/{trigger.namespace}/{trigger.name}",
                value={"phase": phase, "restart_count": restart_count, "conditions": conditions},
                observed_at=datetime.now(UTC),
                metadata={},
            )
        ]


if __name__ == "__main__":
    print(PodStatusCollector())
