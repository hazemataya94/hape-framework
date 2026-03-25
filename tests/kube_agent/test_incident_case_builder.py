from datetime import UTC, datetime

from services.kube_agent.investigation.case.incident_case_builder import IncidentCaseBuilder
from services.kube_agent.investigation.checks.diagnostic_check_models import CheckResult
from services.kube_agent.investigation.evidence.evidence_models import EvidenceBundle, EvidenceItem
from services.kube_agent.investigation.triggers.trigger_models import Trigger


def test_incident_case_builder_sets_likely_causes_and_recommendations() -> None:
    trigger = Trigger(type="pod", cluster="demo", namespace="payments", name="api")
    evidence = EvidenceBundle(
        trigger=trigger,
        items=[
            EvidenceItem(
                key="kubernetes.pod.events",
                source="kubernetes",
                resource_ref="pod/payments/api",
                value=[{"reason": "Killing", "message": "OOMKilled"}],
                observed_at=datetime.now(UTC),
                metadata={},
            )
        ],
        links={"Pod dashboard": "http://grafana.local/d/pod"},
    )
    check_results = [
        CheckResult(
            check_name="oom-kill",
            status="matched",
            confidence="high",
            summary="Pod restart appears linked to OOMKilled events.",
            evidence_keys=["kubernetes.pod.events"],
            details={},
        )
    ]
    incident_case_builder = IncidentCaseBuilder()
    incident_case = incident_case_builder.build(trigger=trigger, evidence=evidence, check_results=check_results)
    assert "oom-kill" in incident_case.likely_causes
    assert incident_case.recommendations
    assert incident_case.dashboard_links["Pod dashboard"] == "http://grafana.local/d/pod"


def test_incident_case_builder_keeps_hypotheses_for_mixed_results() -> None:
    trigger = Trigger(type="pod", cluster="demo", namespace="payments", name="api")
    evidence = EvidenceBundle(
        trigger=trigger,
        items=[EvidenceItem(key="kubernetes.pod.events", source="kubernetes", resource_ref="pod/payments/api", value=[], observed_at=datetime.now(UTC), metadata={})],
        links={"Pod dashboard": "http://grafana.local/d/pod"},
    )
    check_results = [
        CheckResult(
            check_name="oom-kill",
            status="matched",
            confidence="high",
            summary="OOM signal.",
            evidence_keys=["kubernetes.pod.events"],
            details={},
        ),
        CheckResult(
            check_name="probe-failure",
            status="inconclusive",
            confidence="medium",
            summary="Probe signal is weak.",
            evidence_keys=["kubernetes.pod.events"],
            details={},
        ),
    ]
    incident_case_builder = IncidentCaseBuilder()
    incident_case = incident_case_builder.build(trigger=trigger, evidence=evidence, check_results=check_results)
    assert "oom-kill" in incident_case.likely_causes
    assert any("probe-failure" in item for item in incident_case.hypotheses)


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main(["-q", __file__]))
