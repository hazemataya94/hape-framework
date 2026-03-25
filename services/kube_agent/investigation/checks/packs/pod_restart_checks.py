from services.kube_agent.investigation.checks.base_check import BaseCheck
from services.kube_agent.investigation.checks.diagnostic_check_models import CheckResult
from services.kube_agent.investigation.evidence.evidence_models import EvidenceBundle
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class OomKillCheck(BaseCheck):
    CHECK_NAME = "oom-kill"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        values = self._find_evidence_values(evidence=evidence, key="kubernetes.pod.events")
        matched = self._contains_text(values=values, expected_text="oomkilled")
        return CheckResult(check_name=self.CHECK_NAME, status="matched" if matched else "not_matched", confidence="high" if matched else "low", summary="Pod restart appears linked to OOMKilled events." if matched else "No OOMKilled signal in pod events.", evidence_keys=["kubernetes.pod.events"], details={})


class ProbeFailureCheck(BaseCheck):
    CHECK_NAME = "probe-failure"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        values = self._find_evidence_values(evidence=evidence, key="kubernetes.pod.events")
        matched = self._contains_text(values=values, expected_text="probe")
        return CheckResult(check_name=self.CHECK_NAME, status="matched" if matched else "not_matched", confidence="medium" if matched else "low", summary="Probe failure pattern found in pod events." if matched else "No probe failure pattern found.", evidence_keys=["kubernetes.pod.events"], details={})


class EvictionCheck(BaseCheck):
    CHECK_NAME = "eviction"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        values = self._find_evidence_values(evidence=evidence, key="kubernetes.pod.events")
        matched = self._contains_text(values=values, expected_text="evicted")
        return CheckResult(check_name=self.CHECK_NAME, status="matched" if matched else "not_matched", confidence="medium" if matched else "low", summary="Pod was evicted." if matched else "No eviction pattern found.", evidence_keys=["kubernetes.pod.events"], details={})


class UnexpectedExitCodeCheck(BaseCheck):
    CHECK_NAME = "unexpected-exit-code"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        values = self._find_evidence_values(evidence=evidence, key="kubernetes.pod.logs")
        matched = self._contains_text(values=values, expected_text="exit code")
        return CheckResult(check_name=self.CHECK_NAME, status="matched" if matched else "inconclusive", confidence="medium" if matched else "low", summary="Pod logs show an exit code signal." if matched else "No clear exit-code signal in logs.", evidence_keys=["kubernetes.pod.logs"], details={})


if __name__ == "__main__":
    print(OomKillCheck.CHECK_NAME)
