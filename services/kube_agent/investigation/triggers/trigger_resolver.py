from typing import Any

from core.errors.exceptions import HapeValidationError
from services.kube_agent.investigation.triggers.trigger_models import Trigger
from services.kube_agent.investigation.triggers.trigger_parser import TriggerParser


class TriggerResolver:
    def __init__(self, trigger_parser: TriggerParser | None = None) -> None:
        self.trigger_parser = trigger_parser or TriggerParser()

    def _validate_common_fields(self, normalized_trigger: dict[str, Any]) -> None:
        if not normalized_trigger.get("type"):
            raise HapeValidationError(code="KUBE_AGENT_TRIGGER_KIND_REQUIRED", message="Trigger field 'type' is required.")
        if not normalized_trigger.get("cluster"):
            raise HapeValidationError(code="KUBE_AGENT_TRIGGER_CLUSTER_REQUIRED", message="Trigger field 'cluster' is required.")

    def _validate_kind_specific_fields(self, normalized_trigger: dict[str, Any]) -> None:
        trigger_type = normalized_trigger["type"]
        name = normalized_trigger.get("name")
        if trigger_type in {"pod", "deployment", "node", "alert", "cost"} and not name:
            raise HapeValidationError(code="KUBE_AGENT_TRIGGER_NAME_REQUIRED", message=f"Trigger name field is required for type '{trigger_type}'.")
        if trigger_type in {"pod", "deployment", "cost"} and not normalized_trigger.get("namespace"):
            raise HapeValidationError(code="KUBE_AGENT_TRIGGER_NAMESPACE_REQUIRED", message=f"Trigger namespace is required for type '{trigger_type}'.")

    def resolve(self, raw_trigger: dict[str, Any]) -> Trigger:
        normalized_trigger = self.trigger_parser.parse(raw_trigger=raw_trigger)
        self._validate_common_fields(normalized_trigger=normalized_trigger)
        self._validate_kind_specific_fields(normalized_trigger=normalized_trigger)
        return Trigger(
            type=normalized_trigger["type"],
            cluster=normalized_trigger["cluster"],
            namespace=normalized_trigger["namespace"],
            name=normalized_trigger["name"],
            source=normalized_trigger["source"],
            labels=normalized_trigger["labels"],
            annotations=normalized_trigger["annotations"],
            metadata=normalized_trigger["metadata"],
        )


if __name__ == "__main__":
    trigger_resolver = TriggerResolver()
    print(trigger_resolver.resolve({"type": "pod", "cluster": "demo", "namespace": "default", "pod": "api"}))
