from __future__ import annotations

import hashlib
import json

from services.kube_agent.investigation.case.hypothesis_builder import HypothesisBuilder
from services.kube_agent.investigation.case.incident_case_models import IncidentCase
from services.kube_agent.investigation.case.recommendation_builder import RecommendationBuilder
from services.kube_agent.investigation.checks.diagnostic_check_models import CheckResult
from services.kube_agent.investigation.evidence.evidence_models import EvidenceBundle
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class IncidentCaseBuilder:
    def __init__(self, hypothesis_builder: HypothesisBuilder | None = None, recommendation_builder: RecommendationBuilder | None = None) -> None:
        self.hypothesis_builder = hypothesis_builder or HypothesisBuilder()
        self.recommendation_builder = recommendation_builder or RecommendationBuilder()

    @staticmethod
    def _build_case_id(trigger: Trigger, check_results: list[CheckResult]) -> str:
        payload = {
            "type": trigger.type,
            "cluster": trigger.cluster,
            "namespace": trigger.namespace,
            "name": trigger.name,
            "checks": [f"{item.check_name}:{item.status}" for item in check_results],
        }
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        return digest[:16]

    @staticmethod
    def _build_title(trigger: Trigger) -> str:
        if trigger.namespace:
            return f"{trigger.type} incident: {trigger.namespace}/{trigger.name}"
        return f"{trigger.type} incident: {trigger.name}"

    @staticmethod
    def _build_likely_causes(check_results: list[CheckResult]) -> list[str]:
        return [check_result.check_name for check_result in check_results if check_result.status == "matched"]

    @staticmethod
    def _build_summary(trigger: Trigger, likely_causes: list[str], check_results: list[CheckResult]) -> str:
        if trigger.type == "cost":
            matched_summaries = [item.summary for item in check_results if item.status == "matched"]
            if matched_summaries:
                return "Cost analysis findings: " + " ".join(matched_summaries)
            return f"No cost increases or threshold anomalies detected for {trigger.type} '{trigger.name}'."
        if likely_causes:
            causes_text = ", ".join(likely_causes)
            return f"Detected {len(likely_causes)} likely cause(s) for {trigger.type} '{trigger.name}': {causes_text}."
        return f"No deterministic root cause matched for {trigger.type} '{trigger.name}'."

    @staticmethod
    def _build_related_resources(evidence: EvidenceBundle) -> list[str]:
        resource_refs = [item.resource_ref for item in evidence.items if item.resource_ref]
        return sorted(set(resource_refs))

    def build(self, trigger: Trigger, evidence: EvidenceBundle, check_results: list[CheckResult]) -> IncidentCase:
        likely_causes = self._build_likely_causes(check_results=check_results)
        summary = self._build_summary(trigger=trigger, likely_causes=likely_causes, check_results=check_results)
        hypotheses = self.hypothesis_builder.build(check_results=check_results)
        recommendations = self.recommendation_builder.build(check_results=check_results)
        return IncidentCase(
            case_id=self._build_case_id(trigger=trigger, check_results=check_results),
            title=self._build_title(trigger=trigger),
            summary=summary,
            trigger=trigger,
            evidence=evidence,
            check_results=check_results,
            likely_causes=likely_causes,
            hypotheses=hypotheses,
            recommendations=recommendations,
            related_resources=self._build_related_resources(evidence=evidence),
            dashboard_links=evidence.links,
        )


if __name__ == "__main__":
    print(IncidentCaseBuilder())
