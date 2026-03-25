import hashlib

from services.kube_agent.investigation.case.incident_case_models import IncidentCase
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class IncidentFingerprint:
    @staticmethod
    def build(trigger: Trigger, incident_case: IncidentCase | None = None) -> str:
        cause_signature = "unknown"
        if incident_case and incident_case.likely_causes:
            cause_signature = incident_case.likely_causes[0]
        payload = f"{trigger.cluster}|{trigger.namespace}|{trigger.type}|{trigger.name}|{cause_signature}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    print(IncidentFingerprint)
