from datetime import UTC, datetime

from services.kube_agent.investigation.evidence.evidence_models import EvidenceItem
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class PodEventsCollector:
    MAX_EVENTS = 30

    def _build_event_payload(self, events: list) -> list[dict[str, str]]:
        payload: list[dict[str, str]] = []
        for event in events[: self.MAX_EVENTS]:
            payload.append({"reason": str(getattr(event, "reason", "")), "message": str(getattr(event, "message", "")), "type": str(getattr(event, "type", "")), "count": str(getattr(event, "count", ""))})
        return payload

    def collect(self, trigger: Trigger, kubernetes_client) -> list[EvidenceItem]:
        if trigger.type != "pod" or not trigger.namespace:
            return []
        events = kubernetes_client.list_pod_events(namespace=trigger.namespace, pod_name=trigger.name)
        payload = self._build_event_payload(events=events)
        return [
            EvidenceItem(
                key="kubernetes.pod.events",
                source="kubernetes",
                resource_ref=f"pod/{trigger.namespace}/{trigger.name}",
                value=payload,
                observed_at=datetime.now(UTC),
                metadata={"event_count": len(payload)},
            )
        ]


if __name__ == "__main__":
    print(PodEventsCollector())
