from datetime import UTC, datetime

from services.kube_agent.investigation.evidence.evidence_models import EvidenceItem
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class WorkloadOwnerCollector:
    def collect(self, trigger: Trigger, kubernetes_client) -> list[EvidenceItem]:
        if trigger.type != "pod" or not trigger.namespace:
            return []
        owner = kubernetes_client.get_pod_owner(namespace=trigger.namespace, pod_name=trigger.name)
        if not owner:
            return []
        return [
            EvidenceItem(
                key="kubernetes.pod.owner",
                source="kubernetes",
                resource_ref=f"pod/{trigger.namespace}/{trigger.name}",
                value=owner,
                observed_at=datetime.now(UTC),
                metadata={},
            )
        ]


if __name__ == "__main__":
    print(WorkloadOwnerCollector())
