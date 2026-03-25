from datetime import UTC, datetime

from services.kube_agent.investigation.evidence.evidence_models import EvidenceItem
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class RolloutHistoryCollector:
    def _resolve_deployment_name(self, trigger: Trigger, kubernetes_client) -> str | None:
        if trigger.type == "deployment":
            return trigger.name
        if trigger.type != "pod" or not trigger.namespace:
            return None
        owner = kubernetes_client.get_pod_owner(namespace=trigger.namespace, pod_name=trigger.name)
        if not owner:
            return None
        owner_kind = str(owner.get("kind", ""))
        if owner_kind == "ReplicaSet":
            owner_name = str(owner.get("name", ""))
            return owner_name.rsplit("-", 1)[0] if "-" in owner_name else owner_name
        if owner_kind == "Deployment":
            return str(owner.get("name", ""))
        return None

    def collect(self, trigger: Trigger, kubernetes_client) -> list[EvidenceItem]:
        if not trigger.namespace:
            return []
        deployment_name = self._resolve_deployment_name(trigger=trigger, kubernetes_client=kubernetes_client)
        if not deployment_name:
            return []
        rollout_history = kubernetes_client.get_replicaset_history(namespace=trigger.namespace, deployment_name=deployment_name)
        return [
            EvidenceItem(
                key="kubernetes.deployment.rollout_history",
                source="kubernetes",
                resource_ref=f"deployment/{trigger.namespace}/{deployment_name}",
                value=rollout_history,
                observed_at=datetime.now(UTC),
                metadata={},
            )
        ]


if __name__ == "__main__":
    print(RolloutHistoryCollector())
