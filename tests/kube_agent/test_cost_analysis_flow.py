from services.kube_agent.investigation.checks.diagnostic_check_engine import DiagnosticCheckEngine
from services.kube_agent.investigation.evidence.evidence_bundle_builder import EvidenceBundleBuilder
from services.kube_agent.investigation.evidence.prometheus_evidence_collector import PrometheusEvidenceCollector
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class _FakePrometheusClient:
    def query(self, promql: str) -> dict:
        if "hape_eks_deployment_cost_exporter_up" in promql:
            return {"status": "success", "data": {"resultType": "vector", "result": [{"metric": {}, "value": [1, "1"]}]}}
        if 'hape_eks_deployment_cost_total_usd{period="hourly"} offset 1h' in promql:
            return {"status": "success", "data": {"resultType": "vector", "result": [{"metric": {"period": "hourly"}, "value": [1, "10"]}]}}
        if 'hape_eks_deployment_cost_total_usd{period="hourly"}' in promql:
            return {"status": "success", "data": {"resultType": "vector", "result": [{"metric": {"period": "hourly"}, "value": [1, "40"]}]}}
        if 'hape_eks_deployment_cost_workload_max_hourly_usd{namespace="payments",name="api"}' in promql:
            return {"status": "success", "data": {"resultType": "vector", "result": [{"metric": {"namespace": "payments", "name": "api"}, "value": [1, "12"]}]}}
        if "topk(" in promql and "offset 1h" in promql:
            return {
                "status": "success",
                "data": {
                    "resultType": "vector",
                    "result": [
                        {"metric": {"namespace": "payments", "name": "api"}, "value": [1, "9"]},
                        {"metric": {"namespace": "payments", "name": "worker"}, "value": [1, "6"]},
                    ],
                },
            }
        if "topk(" in promql:
            return {
                "status": "success",
                "data": {
                    "resultType": "vector",
                    "result": [
                        {"metric": {"namespace": "payments", "name": "api"}, "value": [1, "12"]},
                        {"metric": {"namespace": "payments", "name": "worker"}, "value": [1, "7"]},
                    ],
                },
            }
        return {"status": "success", "data": {"resultType": "vector", "result": []}}


def test_cost_prometheus_evidence_collection() -> None:
    trigger = Trigger(type="cost", cluster="demo", namespace="payments", name="api", metadata={"historical_offset": "1h"})
    collector = PrometheusEvidenceCollector()
    items = collector.collect(trigger=trigger, prometheus_client=_FakePrometheusClient())
    keys = {item.key for item in items}
    assert "prometheus.cost.exporter_up" in keys
    assert "prometheus.cost.total_hourly_usd" in keys
    assert "prometheus.cost.total_hourly_usd.offset" in keys
    assert "prometheus.cost.workload_hourly_usd" in keys
    assert "prometheus.cost.top_workloads_hourly_usd" in keys


def test_cost_check_engine_matches_threshold_and_ratio() -> None:
    trigger = Trigger(type="cost", cluster="demo", namespace="payments", name="api", metadata={"historical_offset": "1h"})
    collector = PrometheusEvidenceCollector()
    items = collector.collect(trigger=trigger, prometheus_client=_FakePrometheusClient())
    evidence = EvidenceBundleBuilder().build(trigger=trigger, items=items, links={})
    results = DiagnosticCheckEngine().run(trigger=trigger, evidence=evidence)
    results_by_name = {result.check_name: result for result in results}
    assert results_by_name["cost-exporter-unavailable"].status == "not_matched"
    assert results_by_name["cost-total-hourly-threshold"].status == "matched"
    assert results_by_name["cost-workload-hourly-threshold"].status == "matched"
    assert results_by_name["cost-hourly-increase-ratio"].status == "matched"
    assert results_by_name["cost-top-workloads-increase"].status == "matched"


def test_cost_all_workloads_mode_finds_increased_workloads() -> None:
    trigger = Trigger(type="cost", cluster="demo", namespace="payments", name="__all__", metadata={"historical_offset": "1h", "all_workloads": True})
    collector = PrometheusEvidenceCollector()
    items = collector.collect(trigger=trigger, prometheus_client=_FakePrometheusClient())
    evidence = EvidenceBundleBuilder().build(trigger=trigger, items=items, links={})
    results = DiagnosticCheckEngine().run(trigger=trigger, evidence=evidence)
    results_by_name = {result.check_name: result for result in results}
    assert results_by_name["cost-workload-hourly-threshold"].status == "not_matched"
    assert results_by_name["cost-top-workloads-increase"].status == "matched"
    assert "payments/api" in results_by_name["cost-top-workloads-increase"].summary

