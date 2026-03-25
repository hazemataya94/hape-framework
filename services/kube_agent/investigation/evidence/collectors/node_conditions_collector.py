from datetime import UTC, datetime

from services.kube_agent.investigation.evidence.evidence_models import EvidenceItem
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class NodeConditionsCollector:
    def _resolve_node_name(self, trigger: Trigger, kubernetes_client) -> str | None:
        if trigger.type == "node":
            return trigger.name
        if trigger.type == "pod" and trigger.namespace:
            pod = kubernetes_client.get_pod(namespace=trigger.namespace, pod_name=trigger.name)
            if pod.spec and pod.spec.node_name:
                return pod.spec.node_name
        return None

    def collect(self, trigger: Trigger, kubernetes_client) -> list[EvidenceItem]:
        node_name = self._resolve_node_name(trigger=trigger, kubernetes_client=kubernetes_client)
        if not node_name:
            return []
        node = kubernetes_client.get_node(node_name=node_name)
        conditions_payload: list[dict[str, str]] = []
        for condition in node.status.conditions or []:
            conditions_payload.append({"type": str(condition.type), "status": str(condition.status), "reason": str(condition.reason), "message": str(condition.message)})
        return [
            EvidenceItem(
                key="kubernetes.node.conditions",
                source="kubernetes",
                resource_ref=f"node/{node_name}",
                value=conditions_payload,
                observed_at=datetime.now(UTC),
                metadata={},
            )
        ]


if __name__ == "__main__":
    print(NodeConditionsCollector())
