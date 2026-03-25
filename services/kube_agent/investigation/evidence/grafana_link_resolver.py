from services.kube_agent.investigation.triggers.trigger_models import Trigger


class GrafanaLinkResolver:
    def _resolve_resource_inputs(self, trigger: Trigger) -> tuple[str | None, str | None, str | None]:
        namespace = trigger.namespace
        workload_name: str | None = None
        node_name: str | None = None
        if trigger.type in {"pod", "deployment", "cost"}:
            workload_name = trigger.name
        elif trigger.type == "node":
            node_name = trigger.name
        elif trigger.type == "alert":
            workload_name = trigger.labels.get("pod") or trigger.labels.get("deployment")
            node_name = trigger.labels.get("node")
            namespace = namespace or trigger.labels.get("namespace")
        return namespace, workload_name, node_name

    def resolve(self, trigger: Trigger, grafana_client) -> dict[str, str]:
        namespace, workload_name, node_name = self._resolve_resource_inputs(trigger=trigger)
        return grafana_client.find_dashboard_links(namespace=namespace, workload_name=workload_name, node_name=node_name)


if __name__ == "__main__":
    print(GrafanaLinkResolver())
