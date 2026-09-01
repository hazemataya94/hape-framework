# Kubernetes investigation

## Purpose

Investigate a Kubernetes incident from a CLI trigger.

## Prerequisites

- Cluster access through the local kubeconfig.
- Optional Prometheus, Grafana, or Alertmanager endpoints for richer investigation.
- Local kind labs are documented separately under [infrastructure](../infra/README.md).

## Investigate a pod

```bash
hape kube-agent investigate pod --namespace example-ns --name example-pod
```

Safety level: `read`.

Side effects: reads cluster and optional observability APIs; does not apply workload changes.

## List stored incidents

```bash
hape kube-agent incidents list
```

Safety level: `read`.

## Local labs versus production

Use `make kind-up` only for local lab reproduction.

Do not point production clusters at local hostnames.

## Related documentation

- [Kube-agent CLI](../cli/kube-agent.md)
- [Kube-agent service](../services/kube-agent-service.md)
- [Kube-agent architecture](../architectures/kube_agent_architecture.md)
- [Kube-agent fixtures](../infra/kube-agent-fixtures.md)
