from services.kube_agent.investigation.evidence.collectors.node_conditions_collector import NodeConditionsCollector
from services.kube_agent.investigation.evidence.collectors.pod_events_collector import PodEventsCollector
from services.kube_agent.investigation.evidence.collectors.pod_logs_collector import PodLogsCollector
from services.kube_agent.investigation.evidence.collectors.pod_status_collector import PodStatusCollector
from services.kube_agent.investigation.evidence.collectors.rollout_history_collector import RolloutHistoryCollector
from services.kube_agent.investigation.evidence.collectors.scheduling_failure_collector import SchedulingFailureCollector
from services.kube_agent.investigation.evidence.collectors.workload_owner_collector import WorkloadOwnerCollector
from services.kube_agent.investigation.evidence.evidence_models import EvidenceItem
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class KubernetesEvidenceCollector:
    def __init__(self) -> None:
        self.pod_status_collector = PodStatusCollector()
        self.pod_events_collector = PodEventsCollector()
        self.pod_logs_collector = PodLogsCollector()
        self.workload_owner_collector = WorkloadOwnerCollector()
        self.rollout_history_collector = RolloutHistoryCollector()
        self.node_conditions_collector = NodeConditionsCollector()
        self.scheduling_failure_collector = SchedulingFailureCollector()

    def _collect_pod_evidence(self, trigger: Trigger, kubernetes_client) -> list[EvidenceItem]:
        items: list[EvidenceItem] = []
        items.extend(self.pod_status_collector.collect(trigger=trigger, kubernetes_client=kubernetes_client))
        items.extend(self.pod_events_collector.collect(trigger=trigger, kubernetes_client=kubernetes_client))
        items.extend(self.pod_logs_collector.collect(trigger=trigger, kubernetes_client=kubernetes_client))
        items.extend(self.workload_owner_collector.collect(trigger=trigger, kubernetes_client=kubernetes_client))
        items.extend(self.rollout_history_collector.collect(trigger=trigger, kubernetes_client=kubernetes_client))
        items.extend(self.node_conditions_collector.collect(trigger=trigger, kubernetes_client=kubernetes_client))
        items.extend(self.scheduling_failure_collector.collect(trigger=trigger, kubernetes_client=kubernetes_client))
        return items

    def _collect_deployment_evidence(self, trigger: Trigger, kubernetes_client) -> list[EvidenceItem]:
        return self.rollout_history_collector.collect(trigger=trigger, kubernetes_client=kubernetes_client)

    def _collect_node_evidence(self, trigger: Trigger, kubernetes_client) -> list[EvidenceItem]:
        return self.node_conditions_collector.collect(trigger=trigger, kubernetes_client=kubernetes_client)

    def _collect_alert_evidence(self, trigger: Trigger, kubernetes_client) -> list[EvidenceItem]:
        namespace = trigger.labels.get("namespace")
        pod_name = trigger.labels.get("pod")
        if not namespace or not pod_name:
            return []
        synthetic_trigger = Trigger(type="pod", cluster=trigger.cluster, namespace=namespace, name=pod_name, source=trigger.source, labels=trigger.labels, annotations=trigger.annotations, metadata=trigger.metadata)
        return self._collect_pod_evidence(trigger=synthetic_trigger, kubernetes_client=kubernetes_client)

    def collect(self, trigger: Trigger, kubernetes_client) -> list[EvidenceItem]:
        if trigger.type == "pod":
            return self._collect_pod_evidence(trigger=trigger, kubernetes_client=kubernetes_client)
        if trigger.type == "deployment":
            return self._collect_deployment_evidence(trigger=trigger, kubernetes_client=kubernetes_client)
        if trigger.type == "node":
            return self._collect_node_evidence(trigger=trigger, kubernetes_client=kubernetes_client)
        if trigger.type == "alert":
            return self._collect_alert_evidence(trigger=trigger, kubernetes_client=kubernetes_client)
        return []


if __name__ == "__main__":
    print(KubernetesEvidenceCollector())
