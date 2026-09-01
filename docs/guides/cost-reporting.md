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

## Related documentation

- [EKS deployment cost CLI](../cli/eks-deployment-cost.md)
- [EKS deployment cost service](../services/eks-deployment-cost-service.md)
- [EKS deployment cost exporter](../exporters/eks-deployment-cost-exporter.md)
- [Demo](../../demos/eks-deployment-cost/README.md)
