from services.kube_agent.investigation.checks.base_check import BaseCheck
from services.kube_agent.investigation.checks.diagnostic_check_models import CheckResult
from services.kube_agent.config.kube_agent_config import KubeAgentConfig
from services.kube_agent.investigation.evidence.evidence_models import EvidenceBundle
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class _CostCheckBase(BaseCheck):
    def __init__(self) -> None:
        self.config = KubeAgentConfig.load()

    @staticmethod
    def _first_sample_value(values: list) -> float | None:
        if not values:
            return None
        first_group = values[0]
        if not isinstance(first_group, list) or not first_group:
            return None
        first_sample = first_group[0]
        if not isinstance(first_sample, dict):
            return None
        sample_value = first_sample.get("value")
        if not isinstance(sample_value, (int, float)):
            return None
        return float(sample_value)

    def _not_applicable(self, summary: str, evidence_keys: list[str]) -> CheckResult:
        return CheckResult(check_name=self.CHECK_NAME, status="not_matched", confidence="low", summary=summary, evidence_keys=evidence_keys, details={})

    @staticmethod
    def _workload_key(sample: dict) -> str | None:
        metric = sample.get("metric")
        if not isinstance(metric, dict):
            return None
        namespace = str(metric.get("namespace", "")).strip()
        name = str(metric.get("name", "")).strip()
        if not namespace or not name:
            return None
        return f"{namespace}/{name}"

    @staticmethod
    def _to_workload_map(values: list) -> dict[str, float]:
        if not values:
            return {}
        first_group = values[0]
        if not isinstance(first_group, list):
            return {}
        workload_map: dict[str, float] = {}
        for sample in first_group:
            if not isinstance(sample, dict):
                continue
            workload_ref = _CostCheckBase._workload_key(sample=sample)
            if not workload_ref:
                continue
            sample_value = sample.get("value")
            if not isinstance(sample_value, (int, float)):
                continue
            workload_map[workload_ref] = float(sample_value)
        return workload_map


class CostExporterAvailabilityCheck(_CostCheckBase):
    CHECK_NAME = "cost-exporter-unavailable"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        evidence_keys = ["prometheus.cost.exporter_up"]
        if trigger.type != "cost":
            return self._not_applicable(summary="Cost exporter availability check is not applicable for this trigger.", evidence_keys=evidence_keys)
        exporter_values = self._find_evidence_values(evidence=evidence, key="prometheus.cost.exporter_up")
        exporter_up = self._first_sample_value(values=exporter_values)
        if exporter_up is None:
            return CheckResult(check_name=self.CHECK_NAME, status="inconclusive", confidence="low", summary="Cost exporter health metric is missing.", evidence_keys=evidence_keys, details={})
        if exporter_up < 1:
            return CheckResult(check_name=self.CHECK_NAME, status="matched", confidence="high", summary="Cost exporter reports degraded state.", evidence_keys=evidence_keys, details={"exporter_up": exporter_up})
        return CheckResult(check_name=self.CHECK_NAME, status="not_matched", confidence="high", summary="Cost exporter reports healthy state.", evidence_keys=evidence_keys, details={"exporter_up": exporter_up})


class CostTotalHourlyThresholdCheck(_CostCheckBase):
    CHECK_NAME = "cost-total-hourly-threshold"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        evidence_keys = ["prometheus.cost.total_hourly_usd"]
        if trigger.type != "cost":
            return self._not_applicable(summary="Total hourly cost threshold check is not applicable for this trigger.", evidence_keys=evidence_keys)
        total_values = self._find_evidence_values(evidence=evidence, key="prometheus.cost.total_hourly_usd")
        total_hourly_usd = self._first_sample_value(values=total_values)
        if total_hourly_usd is None:
            return CheckResult(check_name=self.CHECK_NAME, status="inconclusive", confidence="low", summary="Total hourly cost metric is missing.", evidence_keys=evidence_keys, details={})
        threshold = self.config.cost_total_hourly_usd_threshold
        matched = total_hourly_usd > threshold
        return CheckResult(
            check_name=self.CHECK_NAME,
            status="matched" if matched else "not_matched",
            confidence="high" if matched else "medium",
            summary=f"Total hourly cost {total_hourly_usd:.2f} USD is {'above' if matched else 'within'} threshold {threshold:.2f} USD.",
            evidence_keys=evidence_keys,
            details={"total_hourly_usd": total_hourly_usd, "threshold": threshold},
        )


class CostWorkloadHourlyThresholdCheck(_CostCheckBase):
    CHECK_NAME = "cost-workload-hourly-threshold"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        evidence_keys = ["prometheus.cost.workload_hourly_usd"]
        if trigger.type != "cost":
            return self._not_applicable(summary="Workload hourly cost threshold check is not applicable for this trigger.", evidence_keys=evidence_keys)
        if bool(trigger.metadata.get("all_workloads")):
            return self._not_applicable(summary="Workload-specific threshold check is skipped in all-workloads mode.", evidence_keys=evidence_keys)
        workload_values = self._find_evidence_values(evidence=evidence, key="prometheus.cost.workload_hourly_usd")
        workload_hourly_usd = self._first_sample_value(values=workload_values)
        if workload_hourly_usd is None:
            return CheckResult(check_name=self.CHECK_NAME, status="inconclusive", confidence="low", summary=f"Workload hourly metric is missing for deployment '{trigger.name}'.", evidence_keys=evidence_keys, details={})
        threshold = self.config.cost_workload_hourly_usd_threshold
        matched = workload_hourly_usd > threshold
        return CheckResult(
            check_name=self.CHECK_NAME,
            status="matched" if matched else "not_matched",
            confidence="high" if matched else "medium",
            summary=f"Deployment hourly cost {workload_hourly_usd:.2f} USD is {'above' if matched else 'within'} threshold {threshold:.2f} USD.",
            evidence_keys=evidence_keys,
            details={"deployment_hourly_usd": workload_hourly_usd, "threshold": threshold},
        )


class CostHourlyIncreaseRatioCheck(_CostCheckBase):
    CHECK_NAME = "cost-hourly-increase-ratio"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        evidence_keys = ["prometheus.cost.total_hourly_usd", "prometheus.cost.total_hourly_usd.offset"]
        if trigger.type != "cost":
            return self._not_applicable(summary="Hourly increase ratio check is not applicable for this trigger.", evidence_keys=evidence_keys)
        current_values = self._find_evidence_values(evidence=evidence, key="prometheus.cost.total_hourly_usd")
        previous_values = self._find_evidence_values(evidence=evidence, key="prometheus.cost.total_hourly_usd.offset")
        current_hourly_usd = self._first_sample_value(values=current_values)
        previous_hourly_usd = self._first_sample_value(values=previous_values)
        if current_hourly_usd is None or previous_hourly_usd is None:
            return CheckResult(check_name=self.CHECK_NAME, status="inconclusive", confidence="low", summary="Current or historical hourly cost metric is missing.", evidence_keys=evidence_keys, details={})
        if previous_hourly_usd <= 0:
            return CheckResult(check_name=self.CHECK_NAME, status="inconclusive", confidence="low", summary="Historical hourly cost is zero; increase ratio is not meaningful.", evidence_keys=evidence_keys, details={"current_hourly_usd": current_hourly_usd, "previous_hourly_usd": previous_hourly_usd})
        ratio = current_hourly_usd / previous_hourly_usd
        threshold = self.config.cost_increase_ratio_threshold
        matched = ratio > threshold
        return CheckResult(
            check_name=self.CHECK_NAME,
            status="matched" if matched else "not_matched",
            confidence="high" if matched else "medium",
            summary=f"Hourly cost increase ratio is {ratio:.2f} and is {'above' if matched else 'within'} threshold {threshold:.2f}.",
            evidence_keys=evidence_keys,
            details={"current_hourly_usd": current_hourly_usd, "previous_hourly_usd": previous_hourly_usd, "ratio": ratio, "threshold": threshold},
        )


class CostTopWorkloadsIncreaseCheck(_CostCheckBase):
    CHECK_NAME = "cost-top-workloads-increase"

    def evaluate(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        evidence_keys = ["prometheus.cost.top_workloads_hourly_usd", "prometheus.cost.top_workloads_hourly_usd.offset"]
        if trigger.type != "cost":
            return self._not_applicable(summary="Top workloads increase check is not applicable for this trigger.", evidence_keys=evidence_keys)
        current_values = self._find_evidence_values(evidence=evidence, key="prometheus.cost.top_workloads_hourly_usd")
        previous_values = self._find_evidence_values(evidence=evidence, key="prometheus.cost.top_workloads_hourly_usd.offset")
        current_by_workload = self._to_workload_map(values=current_values)
        previous_by_workload = self._to_workload_map(values=previous_values)
        if not current_by_workload or not previous_by_workload:
            return CheckResult(check_name=self.CHECK_NAME, status="inconclusive", confidence="low", summary="Current or historical top workload metrics are missing.", evidence_keys=evidence_keys, details={})

        increases: list[dict[str, float | str]] = []
        for workload_ref, current_value in sorted(current_by_workload.items()):
            previous_value = previous_by_workload.get(workload_ref, 0.0)
            delta = current_value - previous_value
            if delta > 0:
                increases.append({"workload": workload_ref, "current_hourly_usd": round(current_value, 4), "previous_hourly_usd": round(previous_value, 4), "delta_hourly_usd": round(delta, 4)})

        if not increases:
            return CheckResult(check_name=self.CHECK_NAME, status="not_matched", confidence="high", summary="No top workload hourly cost increases detected over the historical window.", evidence_keys=evidence_keys, details={})

        top_increases = sorted(increases, key=lambda item: float(item["delta_hourly_usd"]), reverse=True)[:5]
        summary_items = ", ".join([f"{item['workload']} (+{float(item['delta_hourly_usd']):.2f} USD/h)" for item in top_increases])
        return CheckResult(
            check_name=self.CHECK_NAME,
            status="matched",
            confidence="high",
            summary=f"Detected increased workload costs in the last window: {summary_items}.",
            evidence_keys=evidence_keys,
            details={"increased_workloads": top_increases},
        )


if __name__ == "__main__":
    print(CostTotalHourlyThresholdCheck.CHECK_NAME)
