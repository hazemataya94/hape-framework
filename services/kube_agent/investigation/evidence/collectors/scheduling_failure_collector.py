from datetime import UTC, datetime

from services.kube_agent.investigation.evidence.evidence_models import EvidenceItem
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class SchedulingFailureCollector:
    def collect(self, trigger: Trigger, kubernetes_client) -> list[EvidenceItem]:
        if trigger.type != "pod" or not trigger.namespace:
            return []
        events = kubernetes_client.list_pod_events(namespace=trigger.namespace, pod_name=trigger.name)
        failed_events: list[dict[str, str]] = []
        for event in events:
            reason = str(getattr(event, "reason", ""))
            if reason != "FailedScheduling":
                continue
            failed_events.append({"reason": reason, "message": str(getattr(event, "message", "")), "count": str(getattr(event, "count", ""))})
        return [
            EvidenceItem(
                key="kubernetes.pod.scheduling_failures",
                source="kubernetes",
                resource_ref=f"pod/{trigger.namespace}/{trigger.name}",
                value=failed_events,
                observed_at=datetime.now(UTC),
                metadata={"failure_count": len(failed_events)},
            )
        ]


if __name__ == "__main__":
    print(SchedulingFailureCollector())
