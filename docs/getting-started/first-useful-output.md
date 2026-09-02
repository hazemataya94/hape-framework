# First useful output

## Purpose

Run two read commands that produce reports you can inspect.

This page does not stop at install and `hape config show`.

Do not use `hape init-cicd` on this path.

## Prerequisites

- [Installation](installation.md) completed.
- [Five-minute quick start](five-minute-quickstart.md) completed.
- Kubernetes investigation needs cluster access through the local kubeconfig.
- EKS cost reporting needs AWS read credentials and Kubernetes access, or the local fixtures described in [EKS deployment cost fixtures](../infra/eks-deployment-cost-fixtures.md).
- Sample screenshots are on the matching [guides](../guides/README.md).

Full reproduction folders stay on GitHub.

## Kubernetes investigation

Investigate a pod and write findings reports.

```bash
hape kube-agent investigate pod --namespace example-ns --name example-pod
```

Safety level: `read`.

Side effects: reads cluster and optional observability APIs.

This command does not apply workload changes.

Expected artifacts:

- `kube-agent-findings-summary.txt`
- `kube-agent-findings.json`
- `kube-agent-findings.md`

Example summary screenshot:

![Kube agent findings summary](../../demos/kube-agent/kube-agent-findings-summary.png)

Full kind lab steps stay in the [kube-agent demo](https://github.com/hazemataya94/hape-framework/tree/main/demos/kube-agent).

The task guide is [Kubernetes investigation](../guides/kubernetes-investigation.md).

## EKS cost report

Generate a Deployment and StatefulSet cost report.

```bash
hape eks-deployment-cost report
```

Safety level: `read`.

Side effects: reads AWS and Kubernetes APIs and writes a local report artifact when configured.

This command does not change cluster resources.

Expected artifacts:

- `eks-deployment-cost-summary.json`
- `eks-deployment-cost-details.csv`

Example Grafana screenshot from the demo:

![Grafana dashboard](../../demos/eks-deployment-cost/grafana-dashboard.png)

Full kind and fixture steps stay in the [EKS deployment cost demo](https://github.com/hazemataya94/hape-framework/tree/main/demos/eks-deployment-cost).

The task guide is [Cost reporting](../guides/cost-reporting.md).

## Related documentation

- [Five-minute quick start](five-minute-quickstart.md)
- [Safety basics](safety-basics.md)
- [Kubernetes investigation](../guides/kubernetes-investigation.md)
- [Cost reporting](../guides/cost-reporting.md)
- [Guides](../guides/README.md)
