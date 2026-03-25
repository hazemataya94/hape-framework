from datetime import UTC, datetime

from services.kube_agent.investigation.checks.packs.pod_pending_checks import FailedSchedulingCheck, InsufficientResourceCheck
from services.kube_agent.investigation.checks.packs.pod_restart_checks import OomKillCheck
from services.kube_agent.investigation.checks.packs.probe_failure_checks import ReadinessProbeFailureCheck
from services.kube_agent.investigation.evidence.evidence_models import EvidenceBundle, EvidenceItem
from services.kube_agent.investigation.triggers.trigger_models import Trigger


def _build_evidence(trigger: Trigger, key: str, value: object) -> EvidenceBundle:
    return EvidenceBundle(
        trigger=trigger,
        items=[EvidenceItem(key=key, source="kubernetes", resource_ref=f"pod/{trigger.namespace}/{trigger.name}", value=value, observed_at=datetime.now(UTC), metadata={})],
        links={},
    )


def test_oom_killed_case_returns_matched() -> None:
    trigger = Trigger(type="pod", cluster="demo", namespace="payments", name="api")
    evidence = _build_evidence(trigger=trigger, key="kubernetes.pod.events", value=[{"message": "OOMKilled"}])
    assert OomKillCheck().evaluate(trigger=trigger, evidence=evidence).status == "matched"


def test_readiness_probe_failures_return_matched() -> None:
    trigger = Trigger(type="pod", cluster="demo", namespace="payments", name="api")
    evidence = _build_evidence(
        trigger=trigger,
        key="kubernetes.pod.events",
        value=[{"message": "Readiness probe failed: Get http://127.0.0.1/health"}],
    )
    assert ReadinessProbeFailureCheck().evaluate(trigger=trigger, evidence=evidence).status == "matched"


def test_failed_scheduling_due_to_memory_returns_matched() -> None:
    trigger = Trigger(type="pod", cluster="demo", namespace="payments", name="api")
    failures = [{"reason": "FailedScheduling", "message": "0/3 nodes are available: 3 Insufficient memory."}]
    evidence = _build_evidence(trigger=trigger, key="kubernetes.pod.scheduling_failures", value=failures)
    assert FailedSchedulingCheck().evaluate(trigger=trigger, evidence=evidence).status == "matched"
    assert InsufficientResourceCheck().evaluate(trigger=trigger, evidence=evidence).status == "matched"


def test_no_supporting_evidence_returns_inconclusive_or_not_matched() -> None:
    trigger = Trigger(type="pod", cluster="demo", namespace="payments", name="api")
    empty_events_evidence = _build_evidence(trigger=trigger, key="kubernetes.pod.events", value=[])
    empty_scheduling_evidence = _build_evidence(trigger=trigger, key="kubernetes.pod.scheduling_failures", value=[])
    assert OomKillCheck().evaluate(trigger=trigger, evidence=empty_events_evidence).status == "not_matched"
    assert ReadinessProbeFailureCheck().evaluate(trigger=trigger, evidence=empty_events_evidence).status == "not_matched"
    assert InsufficientResourceCheck().evaluate(trigger=trigger, evidence=empty_scheduling_evidence).status == "inconclusive"


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main(["-q", __file__]))
