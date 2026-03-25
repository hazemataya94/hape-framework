from datetime import UTC, datetime

from services.kube_agent.investigation.case.incident_case_models import IncidentCase
from services.kube_agent.investigation.checks.diagnostic_check_models import CheckResult
from services.kube_agent.investigation.evidence.evidence_models import EvidenceBundle, EvidenceItem
from services.kube_agent.investigation.findings.findings_models import Findings
from services.kube_agent.investigation.memory.incident_fingerprint import IncidentFingerprint
from services.kube_agent.investigation.memory.incident_memory_service import IncidentMemoryService
from services.kube_agent.investigation.triggers.trigger_models import Trigger


def test_memory_service_saves_and_lists_incidents(tmp_path) -> None:
    sqlite_path = str(tmp_path / "kube-agent.sqlite")
    memory_service = IncidentMemoryService(sqlite_path=sqlite_path)
    trigger = Trigger(type="pod", cluster="demo", namespace="payments", name="api")
    incident_case = IncidentCase(
        case_id="case-1",
        title="pod incident: payments/api",
        summary="summary",
        trigger=trigger,
        evidence=EvidenceBundle(
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
            links={},
        ),
        check_results=[
            CheckResult(
                check_name="oom-kill",
                status="matched",
                confidence="high",
                summary="oom",
                evidence_keys=["kubernetes.pod.events"],
                details={},
            )
        ],
        likely_causes=["oom-kill"],
        hypotheses=["oom hypothesis"],
        recommendations=["increase memory"],
        related_resources=["pod/payments/api"],
        dashboard_links={},
    )
    findings = Findings(
        incident_id="case-1",
        title="pod incident",
        summary="summary",
        likely_root_cause="oom-kill",
        evidence_summary=["kubernetes.pod.events"],
        debugging_steps=["check memory"],
        suggested_fixes=["increase memory"],
        dashboard_links={},
        ai_used=False,
    )
    memory_service.save(trigger=trigger, incident_case=incident_case, findings=findings)
    incidents = memory_service.list_incidents()
    assert len(incidents) == 1
    assert incidents[0].occurrence_count == 1
    memory_service.save(trigger=trigger, incident_case=incident_case, findings=findings)
    incidents = memory_service.list_incidents()
    assert incidents[0].occurrence_count == 2


def test_fingerprint_changes_when_cause_changes() -> None:
    trigger = Trigger(type="pod", cluster="demo", namespace="payments", name="api")
    incident_case_a = IncidentCase(
        case_id="a",
        title="a",
        summary="a",
        trigger=trigger,
        evidence=EvidenceBundle(trigger=trigger, items=[], links={}),
        check_results=[],
        likely_causes=["oom-kill"],
        hypotheses=[],
        recommendations=[],
        related_resources=[],
        dashboard_links={},
    )
    incident_case_b = IncidentCase(
        case_id="b",
        title="b",
        summary="b",
        trigger=trigger,
        evidence=EvidenceBundle(trigger=trigger, items=[], links={}),
        check_results=[],
        likely_causes=["probe-failure"],
        hypotheses=[],
        recommendations=[],
        related_resources=[],
        dashboard_links={},
    )
    fingerprint_a = IncidentFingerprint.build(trigger=trigger, incident_case=incident_case_a)
    fingerprint_b = IncidentFingerprint.build(trigger=trigger, incident_case=incident_case_b)
    assert fingerprint_a != fingerprint_b


def test_ai_skip_logic_behaves_as_designed(tmp_path) -> None:
    sqlite_path = str(tmp_path / "kube-agent.sqlite")
    memory_service = IncidentMemoryService(sqlite_path=sqlite_path, ai_stale_after_hours=24)
    trigger = Trigger(type="pod", cluster="demo", namespace="payments", name="api")
    incident_case = IncidentCase(
        case_id="case-ai",
        title="case-ai",
        summary="summary-ai",
        trigger=trigger,
        evidence=EvidenceBundle(trigger=trigger, items=[], links={}),
        check_results=[],
        likely_causes=["oom-kill"],
        hypotheses=[],
        recommendations=[],
        related_resources=[],
        dashboard_links={},
    )
    findings = Findings(
        incident_id="case-ai",
        title="case-ai",
        summary="summary-ai",
        likely_root_cause="oom-kill",
        evidence_summary=[],
        debugging_steps=[],
        suggested_fixes=[],
        dashboard_links={},
        ai_used=True,
    )
    assert memory_service.should_run_ai(trigger=trigger, incident_case=incident_case, previous_incident=None) is True
    memory_service.save(trigger=trigger, incident_case=incident_case, findings=findings)
    previous_incident = memory_service.find_existing(trigger=trigger, incident_case=incident_case)
    assert previous_incident is not None
    assert memory_service.should_run_ai(trigger=trigger, incident_case=incident_case, previous_incident=previous_incident) is False


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main(["-q", __file__]))
