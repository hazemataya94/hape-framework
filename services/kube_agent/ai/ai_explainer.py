from services.kube_agent.ai.ai_models import AiExplanation
from services.kube_agent.ai.ai_prompt_builder import AiPromptBuilder
from services.kube_agent.ai.ai_response_parser import AiResponseParser
from services.kube_agent.investigation.case.incident_case_models import IncidentCase


class AiExplainer:
    def __init__(self, ai_prompt_builder: AiPromptBuilder | None = None, ai_response_parser: AiResponseParser | None = None) -> None:
        self.ai_prompt_builder = ai_prompt_builder or AiPromptBuilder()
        self.ai_response_parser = ai_response_parser or AiResponseParser()

    def explain(self, incident_case: IncidentCase) -> AiExplanation:
        # Placeholder deterministic fallback until provider wiring is added.
        _ = self.ai_prompt_builder.build(incident_case=incident_case)
        return self.ai_response_parser.parse(
            {
                "summary": incident_case.summary,
                "possible_root_cause": incident_case.likely_causes[0] if incident_case.likely_causes else "",
                "reasoning": "Generated from deterministic checks without external AI provider.",
                "debugging_steps": ";".join(incident_case.hypotheses[:3]),
                "suggested_fixes": ";".join(incident_case.recommendations[:3]),
            }
        )


if __name__ == "__main__":
    print(AiExplainer())
