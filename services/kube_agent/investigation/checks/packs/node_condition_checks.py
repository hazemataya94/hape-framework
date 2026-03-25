from services.kube_agent.investigation.checks.base_check import BaseCheck
from services.kube_agent.investigation.checks.diagnostic_check_models import CheckResult
from services.kube_agent.investigation.evidence.evidence_models import EvidenceBundle
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class MemoryPressureCheck(BaseCheck):
    CHECK_NAME = "memory-pressure"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        values = self._find_evidence_values(evidence=evidence, key="kubernetes.node.conditions")
        matched = self._contains_text(values=values, expected_text="memorypressure") and self._contains_text(values=values, expected_text="true")
        return CheckResult(check_name=self.CHECK_NAME, status="matched" if matched else "not_matched", confidence="high" if matched else "low", summary="Node has memory pressure." if matched else "No memory pressure signal.", evidence_keys=["kubernetes.node.conditions"], details={})


class DiskPressureCheck(BaseCheck):
    CHECK_NAME = "disk-pressure"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        values = self._find_evidence_values(evidence=evidence, key="kubernetes.node.conditions")
        matched = self._contains_text(values=values, expected_text="diskpressure") and self._contains_text(values=values, expected_text="true")
        return CheckResult(check_name=self.CHECK_NAME, status="matched" if matched else "not_matched", confidence="high" if matched else "low", summary="Node has disk pressure." if matched else "No disk pressure signal.", evidence_keys=["kubernetes.node.conditions"], details={})


class PidPressureCheck(BaseCheck):
    CHECK_NAME = "pid-pressure"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        values = self._find_evidence_values(evidence=evidence, key="kubernetes.node.conditions")
        matched = self._contains_text(values=values, expected_text="pidpressure") and self._contains_text(values=values, expected_text="true")
        return CheckResult(check_name=self.CHECK_NAME, status="matched" if matched else "not_matched", confidence="high" if matched else "low", summary="Node has PID pressure." if matched else "No PID pressure signal.", evidence_keys=["kubernetes.node.conditions"], details={})


class NodeNotReadyCheck(BaseCheck):
    CHECK_NAME = "node-not-ready"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        values = self._find_evidence_values(evidence=evidence, key="kubernetes.node.conditions")
        matched = self._contains_text(values=values, expected_text="ready") and self._contains_text(values=values, expected_text="false")
        return CheckResult(check_name=self.CHECK_NAME, status="matched" if matched else "not_matched", confidence="high" if matched else "low", summary="Node is not ready." if matched else "Node readiness signal looks normal.", evidence_keys=["kubernetes.node.conditions"], details={})


if __name__ == "__main__":
    print(NodeNotReadyCheck.CHECK_NAME)
