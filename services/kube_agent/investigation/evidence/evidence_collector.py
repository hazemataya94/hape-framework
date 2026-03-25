from datetime import UTC, datetime

from services.kube_agent.investigation.evidence.collectors.grafana_default_dashboards_collector import GrafanaDefaultDashboardsCollector
from services.kube_agent.investigation.evidence.evidence_bundle_builder import EvidenceBundleBuilder
from services.kube_agent.investigation.evidence.evidence_models import EvidenceBundle
from services.kube_agent.investigation.evidence.evidence_models import EvidenceItem
from services.kube_agent.investigation.evidence.grafana_link_resolver import GrafanaLinkResolver
from services.kube_agent.investigation.evidence.kubernetes_evidence_collector import KubernetesEvidenceCollector
from services.kube_agent.investigation.evidence.prometheus_evidence_collector import PrometheusEvidenceCollector
from services.kube_agent.investigation.triggers.trigger_models import Trigger


class EvidenceCollector:
    def __init__(
        self,
        kubernetes_evidence_collector: KubernetesEvidenceCollector | None = None,
        prometheus_evidence_collector: PrometheusEvidenceCollector | None = None,
        grafana_default_dashboards_collector: GrafanaDefaultDashboardsCollector | None = None,
        grafana_link_resolver: GrafanaLinkResolver | None = None,
        evidence_bundle_builder: EvidenceBundleBuilder | None = None,
    ) -> None:
        self.kubernetes_evidence_collector = kubernetes_evidence_collector or KubernetesEvidenceCollector()
        self.prometheus_evidence_collector = prometheus_evidence_collector or PrometheusEvidenceCollector()
        self.grafana_default_dashboards_collector = grafana_default_dashboards_collector or GrafanaDefaultDashboardsCollector()
        self.grafana_link_resolver = grafana_link_resolver or GrafanaLinkResolver()
        self.evidence_bundle_builder = evidence_bundle_builder or EvidenceBundleBuilder()

    @staticmethod
    def _collect_alertmanager_evidence(trigger: Trigger, alertmanager_client) -> list[EvidenceItem]:
        if trigger.type != "alert":
            return []
        matched_alerts = alertmanager_client.get_alerts_by_labels(matchers=trigger.labels)
        return [
            EvidenceItem(
                key="alertmanager.alerts",
                source="alertmanager",
                resource_ref=f"alert/{trigger.name}",
                value=matched_alerts,
                observed_at=datetime.now(UTC),
                metadata={"matched_count": len(matched_alerts)},
            )
        ]

    def collect(self, trigger: Trigger, kubernetes_client, prometheus_client, alertmanager_client, grafana_client) -> EvidenceBundle:
        items: list[EvidenceItem] = []
        items.extend(self.kubernetes_evidence_collector.collect(trigger=trigger, kubernetes_client=kubernetes_client))
        items.extend(self.prometheus_evidence_collector.collect(trigger=trigger, prometheus_client=prometheus_client))
        items.extend(self._collect_alertmanager_evidence(trigger=trigger, alertmanager_client=alertmanager_client))
        links = self.grafana_default_dashboards_collector.collect(trigger=trigger, evidence_items=items, grafana_client=grafana_client)
        if links:
            items.append(
                EvidenceItem(
                    key="grafana.default_dashboards",
                    source="grafana",
                    resource_ref="grafana/default-dashboards",
                    value=links,
                    observed_at=datetime.now(UTC),
                    metadata={"dashboard_count": len(links)},
                )
            )
        additional_links = self.grafana_link_resolver.resolve(trigger=trigger, grafana_client=grafana_client)
        for link_name, link_url in additional_links.items():
            links.setdefault(link_name, link_url)
        return self.evidence_bundle_builder.build(trigger=trigger, items=items, links=links)


if __name__ == "__main__":
    print(EvidenceCollector())
