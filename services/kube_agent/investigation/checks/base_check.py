from abc import ABC, abstractmethod

from services.kube_agent.investigation.checks.diagnostic_check_models import CheckResult
from services.kube_agent.investigation.evidence.evidence_models import EvidenceBundle
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class BaseCheck(ABC):
    CHECK_NAME = "base-check"

    def _find_evidence_values(self, evidence: EvidenceBundle, key: str) -> list:
        return [item.value for item in evidence.items if item.key == key]

    def _contains_text(self, values: list, expected_text: str) -> bool:
        normalized_expected_text = expected_text.lower()
        return any(normalized_expected_text in str(value).lower() for value in values)

    @abstractmethod
    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        raise NotImplementedError


if __name__ == "__main__":
    print(BaseCheck.CHECK_NAME)
