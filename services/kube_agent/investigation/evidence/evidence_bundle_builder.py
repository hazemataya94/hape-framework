from services.kube_agent.investigation.evidence.evidence_models import EvidenceBundle, EvidenceItem
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class EvidenceBundleBuilder:
    @staticmethod
    def _deduplicate_items(items: list[EvidenceItem]) -> list[EvidenceItem]:
        unique_items: dict[str, EvidenceItem] = {}
        for item in items:
            deduplicate_key = f"{item.key}:{item.resource_ref}:{item.source}"
            unique_items[deduplicate_key] = item
        return list(unique_items.values())

    def build(self, trigger: Trigger, items: list[EvidenceItem], links: dict[str, str] | None = None) -> EvidenceBundle:
        normalized_links = links or {}
        deduplicated_items = self._deduplicate_items(items=items)
        return EvidenceBundle(trigger=trigger, items=deduplicated_items, links=normalized_links)


if __name__ == "__main__":
    print(EvidenceBundleBuilder())
