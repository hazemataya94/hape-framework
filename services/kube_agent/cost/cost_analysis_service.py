from core.errors import HapeValidationError
from core.logging import LocalLogging
from services.kube_agent.investigation.findings.findings_models import Findings
from services.kube_agent.investigation.investigation_service import InvestigationService


class CostAnalysisService:
    DEFAULT_INVESTIGATION_SERVICE: InvestigationService | None = None

    def __init__(self, investigation_service: InvestigationService | None = DEFAULT_INVESTIGATION_SERVICE) -> None:
        self.investigation_service = investigation_service or InvestigationService()
        self.logger = LocalLogging.get_logger("hape.cost_analysis_service")

    def _validate_namespace(self, namespace: str) -> None:
        if not namespace.strip():
            raise HapeValidationError(
                code="KUBE_AGENT_COST_NAMESPACE_REQUIRED",
                message="namespace is required for cost analysis.",
                context={"service": "CostAnalysisService"},
            )

    def analyze(self, kube_context: str, namespace: str, deployment: str | None, all_workloads: bool, historical_offset: str, use_ai: bool) -> Findings:
        self.logger.debug("analyze(kube_context: <str>, namespace: <str>, deployment: <str|none>, all_workloads: <bool>)")
        self._validate_namespace(namespace=namespace)
        target_name = "__all__" if all_workloads else (deployment or "")
        if not target_name.strip():
            raise HapeValidationError(
                code="KUBE_AGENT_COST_TARGET_REQUIRED",
                message="deployment is required unless --all-workloads is set.",
                context={"service": "CostAnalysisService"},
            )
        return self.investigation_service.investigate(
            raw_trigger={
                "type": "cost",
                "cluster": kube_context,
                "namespace": namespace,
                "name": target_name,
                "source": "cli",
                "metadata": {"historical_offset": historical_offset, "all_workloads": all_workloads},
            },
            use_ai=use_ai,
        )


if __name__ == "__main__":
    cost_analysis_service = CostAnalysisService()
    print(cost_analysis_service.__class__.__name__)
