from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from services.kube_agent.investigation.triggers.trigger_models import Trigger


@dataclass(frozen=True)
class EvidenceItem:
    key: str
    source: str
    resource_ref: str
    value: Any
    observed_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceBundle:
    trigger: Trigger
    items: list[EvidenceItem]
    links: dict[str, str] = field(default_factory=dict)


if __name__ == "__main__":
    trigger = Trigger(type="pod", cluster="demo", namespace="default", name="api")
    evidence_item = EvidenceItem(key="pod.phase", source="kubernetes", resource_ref="pod/default/api", value="Running", observed_at=datetime.now(UTC))
    print(EvidenceBundle(trigger=trigger, items=[evidence_item]))
