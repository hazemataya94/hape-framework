from services.kube_agent.ai.ai_models import AiExplanation
from services.kube_agent.investigation.case.incident_case_models import IncidentCase
from services.kube_agent.investigation.findings.findings_models import Findings


class FindingsBuilder:
    @staticmethod
    def _build_evidence_summary(incident_case: IncidentCase) -> list[str]:
        summary_lines: list[str] = []
        for evidence_item in incident_case.evidence.items[:10]:
            summary_lines.append(f"{evidence_item.key}: {evidence_item.resource_ref}")
        return summary_lines

    @staticmethod
    def _build_debugging_steps(incident_case: IncidentCase, ai_explanation: AiExplanation | None) -> list[str]:
        if ai_explanation and ai_explanation.debugging_steps:
            return ai_explanation.debugging_steps
        return incident_case.hypotheses or ["Review pod events and logs for primary error patterns."]

    @staticmethod
    def _build_suggested_fixes(incident_case: IncidentCase, ai_explanation: AiExplanation | None) -> list[str]:
        if ai_explanation and ai_explanation.suggested_fixes:
            return ai_explanation.suggested_fixes
        return incident_case.recommendations

    @staticmethod
    def _build_root_cause(incident_case: IncidentCase, ai_explanation: AiExplanation | None) -> str | None:
        if ai_explanation and ai_explanation.possible_root_cause:
            return ai_explanation.possible_root_cause
        if incident_case.likely_causes:
            return incident_case.likely_causes[0]
        return None

    def build(self, incident_case: IncidentCase, ai_explanation: AiExplanation | None = None) -> Findings:
        return Findings(
            incident_id=incident_case.case_id,
            title=incident_case.title,
            summary=ai_explanation.summary if ai_explanation else incident_case.summary,
            likely_root_cause=self._build_root_cause(incident_case=incident_case, ai_explanation=ai_explanation),
            evidence_summary=self._build_evidence_summary(incident_case=incident_case),
            debugging_steps=self._build_debugging_steps(incident_case=incident_case, ai_explanation=ai_explanation),
            suggested_fixes=self._build_suggested_fixes(incident_case=incident_case, ai_explanation=ai_explanation),
            dashboard_links=incident_case.dashboard_links,
            ai_used=ai_explanation is not None,
        )


if __name__ == "__main__":
    print(FindingsBuilder())
