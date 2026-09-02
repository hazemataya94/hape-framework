# Cost reporting

## Purpose

Generate an EKS Deployment and StatefulSet cost report.

## Prerequisites

- AWS credentials with read access to EKS and pricing data used by the command.
- Kubernetes access to the target cluster.
- Optional local fixtures described in [EKS deployment cost fixtures](../infra/eks-deployment-cost-fixtures.md).

## Generate a report

```bash
hape eks-deployment-cost report
```

Safety level: `read`.

Side effects: reads AWS and Kubernetes APIs; writes a local report artifact when configured.

This command does not change cluster resources.

## Example output

Prometheus exporter metrics:

![Prometheus exporter metrics](../../demos/eks-deployment-cost/prometheus-exporter-metrics.png)

Grafana dashboard:

![Grafana dashboard](../../demos/eks-deployment-cost/grafana-dashboard.png)

## Kube-agent cost analysis

Kube-agent can attach cost findings to a deployment or to all workloads.

Single deployment summary:

![Kube agent cost findings summary](../../demos/kube-agent-cost-analysis/kube-agent-cost-findings-summary-txt.png)

JSON:

![Kube agent cost findings json](../../demos/kube-agent-cost-analysis/kube-agent-cost-findings-json.png)

Markdown:

![Kube agent cost findings markdown](../../demos/kube-agent-cost-analysis/kube-agent-cost-findings-md.png)

Slack:

![Kube agent cost findings slack](../../demos/kube-agent-cost-analysis/kube-agent-cost-findings-slack-txt.png)

All workloads summary:

![Kube agent cost all workloads summary](../../demos/kube-agent-cost-analysis/kube-agent-cost-all-workloads-findings-summary-txt.png)

All workloads JSON:

![Kube agent cost all workloads json](../../demos/kube-agent-cost-analysis/kube-agent-cost-all-workloads-findings-json.png)

All workloads markdown:

![Kube agent cost all workloads markdown](../../demos/kube-agent-cost-analysis/kube-agent-cost-all-workloads-findings-md.png)

All workloads Slack:

![Kube agent cost all workloads slack](../../demos/kube-agent-cost-analysis/kube-agent-cost-all-workloads-findings-slack-txt.png)

## Related documentation

- [First useful output](../getting-started/first-useful-output.md)
- [EKS deployment cost CLI](../cli/eks-deployment-cost.md)
- [EKS deployment cost service](../services/eks-deployment-cost-service.md)
- [EKS deployment cost exporter](../exporters/eks-deployment-cost-exporter.md)
- [EKS deployment cost demo](../../demos/eks-deployment-cost/README.md)
- [Kube-agent cost analysis demo](../../demos/kube-agent-cost-analysis/README.md)
