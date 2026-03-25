from services.kube_agent.investigation.checks.base_check import BaseCheck
from services.kube_agent.investigation.checks.diagnostic_check_models import CheckResult
from services.kube_agent.investigation.evidence.evidence_models import EvidenceBundle
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class DeploymentRevisionChangeCheck(BaseCheck):
    CHECK_NAME = "deployment-revision-change"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        rollout_values = self._find_evidence_values(evidence=evidence, key="kubernetes.deployment.rollout_history")
        latest_history = rollout_values[0] if rollout_values else []
        matched = len(latest_history) >= 2
        return CheckResult(check_name=self.CHECK_NAME, status="matched" if matched else "inconclusive", confidence="medium" if matched else "low", summary="Recent deployment revision change detected." if matched else "No clear revision-change pattern.", evidence_keys=["kubernetes.deployment.rollout_history"], details={})


class ImageChangeCheck(BaseCheck):
    CHECK_NAME = "image-change"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        values = self._find_evidence_values(evidence=evidence, key="kubernetes.pod.events")
        matched = self._contains_text(values=values, expected_text="pulling image")
        return CheckResult(check_name=self.CHECK_NAME, status="matched" if matched else "inconclusive", confidence="medium" if matched else "low", summary="Image change signal found in events." if matched else "No explicit image change signal.", evidence_keys=["kubernetes.pod.events"], details={})


class ConfigChangeCorrelationCheck(BaseCheck):
    CHECK_NAME = "config-change-correlation"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        values = self._find_evidence_values(evidence=evidence, key="kubernetes.pod.events")
        matched = self._contains_text(values=values, expected_text="configmap") or self._contains_text(values=values, expected_text="secret")
        return CheckResult(check_name=self.CHECK_NAME, status="matched" if matched else "inconclusive", confidence="medium" if matched else "low", summary="Config-change signal correlated with incident." if matched else "No config-change correlation signal.", evidence_keys=["kubernetes.pod.events"], details={})


if __name__ == "__main__":
    print(DeploymentRevisionChangeCheck.CHECK_NAME)
