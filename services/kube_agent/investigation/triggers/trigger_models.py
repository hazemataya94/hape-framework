from dataclasses import dataclass, field
from typing import Any, ClassVar

from core.errors.exceptions import HapeValidationError


@dataclass(frozen=True)
class Trigger:
    SUPPORTED_TYPES: ClassVar[set[str]] = {"pod", "deployment", "node", "alert", "cost"}
    SUPPORTED_SOURCES: ClassVar[set[str]] = {"cli", "alertmanager"}

    type: str
    cluster: str
    namespace: str | None
    name: str
    source: str = "cli"
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._validate_type()
        self._validate_source()
        self._validate_required_fields()

    def _validate_type(self) -> None:
        if self.type not in self.SUPPORTED_TYPES:
            raise HapeValidationError(code="KUBE_AGENT_TRIGGER_KIND_INVALID", message=f"Unsupported trigger type '{self.type}'.")

    def _validate_source(self) -> None:
        if self.source not in self.SUPPORTED_SOURCES:
            raise HapeValidationError(code="KUBE_AGENT_TRIGGER_SOURCE_INVALID", message=f"Unsupported trigger source '{self.source}'.")

    def _validate_required_fields(self) -> None:
        if not self.cluster:
            raise HapeValidationError(code="KUBE_AGENT_TRIGGER_CLUSTER_REQUIRED", message="Trigger field 'cluster' is required.")
        if not self.name:
            raise HapeValidationError(code="KUBE_AGENT_TRIGGER_NAME_REQUIRED", message="Trigger field 'name' is required.")
        if self.type in {"pod", "deployment", "cost"} and not self.namespace:
            raise HapeValidationError(code="KUBE_AGENT_TRIGGER_NAMESPACE_REQUIRED", message=f"Trigger field 'namespace' is required for type '{self.type}'.")


if __name__ == "__main__":
    Trigger(type="pod", cluster="demo", namespace="default", name="api", source="cli")
