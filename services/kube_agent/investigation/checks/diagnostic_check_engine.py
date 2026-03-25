from services.kube_agent.investigation.checks.diagnostic_check_models import CheckResult
from services.kube_agent.investigation.checks.registry import DiagnosticCheckRegistry
from services.kube_agent.investigation.evidence.evidence_models import EvidenceBundle
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class DiagnosticCheckEngine:
    def __init__(self, registry: DiagnosticCheckRegistry | None = None) -> None:
        self.registry = registry or DiagnosticCheckRegistry()

    def run(self, trigger: Trigger, evidence: EvidenceBundle) -> list[CheckResult]:
        results: list[CheckResult] = []
        for check in self.registry.get_checks(trigger_type=trigger.type):
            results.append(check.evaluate(trigger=trigger, evidence=evidence))
        return results


if __name__ == "__main__":
    print(DiagnosticCheckEngine())
