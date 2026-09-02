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

## Example output

Summary:

![Kube agent findings summary](../../demos/kube-agent/kube-agent-findings-summary.png)

JSON:

![Kube agent findings json](../../demos/kube-agent/kube-agent-findings-json.png)

Markdown:

![Kube agent findings markdown](../../demos/kube-agent/kube-agent-findings-markdown.png)

Slack:

![Kube agent findings slack](../../demos/kube-agent/kube-agent-findings-slack.png)

## Local labs versus production

Use `make kind-up` only for local lab reproduction.

Do not point production clusters at local hostnames.

## Related documentation

- [First useful output](../getting-started/first-useful-output.md)
- [Kube-agent CLI](../cli/kube-agent.md)
- [Kube-agent service](../services/kube-agent-service.md)
- [Kube-agent architecture](../architectures/kube_agent_architecture.md)
- [Kube-agent fixtures](../infra/kube-agent-fixtures.md)
- [Demo](../../demos/kube-agent/README.md)
