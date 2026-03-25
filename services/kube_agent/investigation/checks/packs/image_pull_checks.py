from services.kube_agent.investigation.checks.base_check import BaseCheck
from services.kube_agent.investigation.checks.diagnostic_check_models import CheckResult
from services.kube_agent.investigation.evidence.evidence_models import EvidenceBundle
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class ImagePullBackOffCheck(BaseCheck):
    CHECK_NAME = "image-pull-backoff"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        values = self._find_evidence_values(evidence=evidence, key="kubernetes.pod.events")
        matched = self._contains_text(values=values, expected_text="imagepullbackoff")
        return CheckResult(check_name=self.CHECK_NAME, status="matched" if matched else "not_matched", confidence="high" if matched else "low", summary="ImagePullBackOff detected." if matched else "No ImagePullBackOff pattern.", evidence_keys=["kubernetes.pod.events"], details={})


class ErrImagePullCheck(BaseCheck):
    CHECK_NAME = "err-image-pull"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        values = self._find_evidence_values(evidence=evidence, key="kubernetes.pod.events")
        matched = self._contains_text(values=values, expected_text="errimagepull")
        return CheckResult(check_name=self.CHECK_NAME, status="matched" if matched else "not_matched", confidence="high" if matched else "low", summary="ErrImagePull detected." if matched else "No ErrImagePull pattern.", evidence_keys=["kubernetes.pod.events"], details={})


if __name__ == "__main__":
    print(ImagePullBackOffCheck.CHECK_NAME)
