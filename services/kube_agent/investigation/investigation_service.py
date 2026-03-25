from typing import Any

from core.errors import HapeError, HapeExternalError, HapeValidationError
from core.logging import LocalLogging
from services.kube_agent.investigation.findings.findings_models import Findings
from services.kube_agent.investigation.investigation_runtime import InvestigationRuntime


class InvestigationService:
    DEFAULT_RUNTIME: InvestigationRuntime | None = None

    def __init__(self, runtime: InvestigationRuntime | None = DEFAULT_RUNTIME) -> None:
        self.runtime = runtime or InvestigationRuntime()
        self.logger = LocalLogging.get_logger("hape.investigation_service")

    def _validate_raw_trigger(self, raw_trigger: dict[str, Any]) -> None:
        if not isinstance(raw_trigger, dict):
            raise HapeValidationError(
                code="KUBE_AGENT_INVESTIGATE_RAW_TRIGGER_INVALID",
                message="raw_trigger must be a dictionary.",
                context={"service": "InvestigationService"},
            )

    def investigate(self, raw_trigger: dict[str, Any], use_ai: bool | None = None) -> Findings:
        self.logger.debug("investigate(raw_trigger: <dict>, use_ai: <bool|none>)")
        self._validate_raw_trigger(raw_trigger=raw_trigger)
        try:
            return self.runtime.investigate(raw_trigger=raw_trigger, use_ai=use_ai)
        except HapeError:
            raise
        except Exception as exc:
            raise HapeExternalError(
                code="KUBE_AGENT_INVESTIGATE_FAILED",
                message="Failed to complete kube-agent investigation flow.",
                context={"service": "InvestigationService", "trigger_type": str(raw_trigger.get("type", ""))},
            ) from exc


if __name__ == "__main__":
    investigation_service = InvestigationService()
    print(investigation_service.__class__.__name__)
