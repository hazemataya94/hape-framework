from datetime import UTC, datetime

from services.kube_agent.investigation.checks.diagnostic_check_engine import DiagnosticCheckEngine
from services.kube_agent.investigation.evidence.evidence_models import EvidenceBundle, EvidenceItem
from services.kube_agent.investigation.triggers.trigger_models import Trigger


def test_oom_kill_check_is_matched_when_event_contains_oomkilled() -> None:
    trigger = Trigger(type="pod", cluster="demo", namespace="payments", name="api")
    evidence = EvidenceBundle(
        trigger=trigger,
        items=[
            EvidenceItem(
                key="kubernetes.pod.events",
                source="kubernetes",
                resource_ref="pod/payments/api",
                value=[{"reason": "Killing", "message": "Container was OOMKilled"}],
                observed_at=datetime.now(UTC),
                metadata={},
            )
        ],
        links={},
    )
    engine = DiagnosticCheckEngine()
    results = engine.run(trigger=trigger, evidence=evidence)
    results_by_name = {result.check_name: result for result in results}
    assert results_by_name["oom-kill"].status == "matched"


def test_failed_scheduling_check_not_matched_without_failures() -> None:
    trigger = Trigger(type="pod", cluster="demo", namespace="payments", name="api")
    evidence = EvidenceBundle(
        trigger=trigger,
        items=[
            EvidenceItem(
                key="kubernetes.pod.scheduling_failures",
                source="kubernetes",
                resource_ref="pod/payments/api",
                value=[],
                observed_at=datetime.now(UTC),
                metadata={},
            )
        ],
        links={},
    )
    engine = DiagnosticCheckEngine()
    results = engine.run(trigger=trigger, evidence=evidence)
    results_by_name = {result.check_name: result for result in results}
    assert results_by_name["failed-scheduling"].status == "not_matched"


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main(["-q", __file__]))
