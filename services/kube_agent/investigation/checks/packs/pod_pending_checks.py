from services.kube_agent.investigation.checks.base_check import BaseCheck
from services.kube_agent.investigation.checks.diagnostic_check_models import CheckResult
from services.kube_agent.investigation.evidence.evidence_models import EvidenceBundle
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class FailedSchedulingCheck(BaseCheck):
    CHECK_NAME = "failed-scheduling"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        values = self._find_evidence_values(evidence=evidence, key="kubernetes.pod.scheduling_failures")
        matched = bool(values and values[0])
        return CheckResult(check_name=self.CHECK_NAME, status="matched" if matched else "not_matched", confidence="high" if matched else "low", summary="Kubernetes reported FailedScheduling events." if matched else "No FailedScheduling events found.", evidence_keys=["kubernetes.pod.scheduling_failures"], details={})


class InsufficientResourceCheck(BaseCheck):
    CHECK_NAME = "insufficient-resource"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        values = self._find_evidence_values(evidence=evidence, key="kubernetes.pod.scheduling_failures")
        matched = self._contains_text(values=values, expected_text="insufficient")
        return CheckResult(check_name=self.CHECK_NAME, status="matched" if matched else "inconclusive", confidence="medium" if matched else "low", summary="Scheduling failures suggest insufficient resources." if matched else "No clear insufficient-resource signal.", evidence_keys=["kubernetes.pod.scheduling_failures"], details={})


class TaintMismatchCheck(BaseCheck):
    CHECK_NAME = "taint-mismatch"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        values = self._find_evidence_values(evidence=evidence, key="kubernetes.pod.scheduling_failures")
        matched = self._contains_text(values=values, expected_text="taint")
        return CheckResult(check_name=self.CHECK_NAME, status="matched" if matched else "inconclusive", confidence="medium" if matched else "low", summary="Scheduling failures mention taints." if matched else "No taint mismatch signal found.", evidence_keys=["kubernetes.pod.scheduling_failures"], details={})


class PvcBindingCheck(BaseCheck):
    CHECK_NAME = "pvc-binding"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        values = self._find_evidence_values(evidence=evidence, key="kubernetes.pod.scheduling_failures")
        matched = self._contains_text(values=values, expected_text="persistentvolumeclaim")
        return CheckResult(check_name=self.CHECK_NAME, status="matched" if matched else "inconclusive", confidence="medium" if matched else "low", summary="Scheduling indicates PVC binding issue." if matched else "No PVC binding issue detected.", evidence_keys=["kubernetes.pod.scheduling_failures"], details={})


class ImagePullFailureCheck(BaseCheck):
    CHECK_NAME = "image-pull-failure"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        values = self._find_evidence_values(evidence=evidence, key="kubernetes.pod.events")
        matched = self._contains_text(values=values, expected_text="imagepull") or self._contains_text(values=values, expected_text="back-off pulling image")
        return CheckResult(check_name=self.CHECK_NAME, status="matched" if matched else "not_matched", confidence="high" if matched else "low", summary="Pod events show image pull failure." if matched else "No image pull failure pattern.", evidence_keys=["kubernetes.pod.events"], details={})


if __name__ == "__main__":
    print(FailedSchedulingCheck.CHECK_NAME)
