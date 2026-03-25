from services.kube_agent.investigation.case.incident_case_models import IncidentCase


class AiPromptBuilder:
    def build(self, incident_case: IncidentCase) -> str:
        return (
            "You are a Kubernetes incident assistant.\n"
            "Use only the provided incident case.\n"
            "Do not invent missing facts.\n"
            "Separate observed facts from hypotheses.\n\n"
            f"Title: {incident_case.title}\n"
            f"Summary: {incident_case.summary}\n"
            f"Likely causes: {incident_case.likely_causes}\n"
            f"Hypotheses: {incident_case.hypotheses}\n"
            f"Recommendations: {incident_case.recommendations}\n"
        )


if __name__ == "__main__":
    print(AiPromptBuilder())
