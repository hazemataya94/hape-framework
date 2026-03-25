from services.kube_agent.investigation.checks.base_check import BaseCheck
from services.kube_agent.investigation.checks.diagnostic_check_models import CheckResult
from services.kube_agent.investigation.evidence.evidence_models import EvidenceBundle
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class ReadinessProbeFailureCheck(BaseCheck):
    CHECK_NAME = "readiness-probe-failure"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        values = self._find_evidence_values(evidence=evidence, key="kubernetes.pod.events")
        matched = self._contains_text(values=values, expected_text="readiness probe failed")
        return CheckResult(check_name=self.CHECK_NAME, status="matched" if matched else "not_matched", confidence="high" if matched else "low", summary="Readiness probe failure detected." if matched else "No readiness probe failure detected.", evidence_keys=["kubernetes.pod.events"], details={})


class LivenessProbeFailureCheck(BaseCheck):
    CHECK_NAME = "liveness-probe-failure"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        values = self._find_evidence_values(evidence=evidence, key="kubernetes.pod.events")
        matched = self._contains_text(values=values, expected_text="liveness probe failed")
        return CheckResult(check_name=self.CHECK_NAME, status="matched" if matched else "not_matched", confidence="high" if matched else "low", summary="Liveness probe failure detected." if matched else "No liveness probe failure detected.", evidence_keys=["kubernetes.pod.events"], details={})


if __name__ == "__main__":
    print(ReadinessProbeFailureCheck.CHECK_NAME)
