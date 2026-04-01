# EKS Deployment Cost

## Purpose
Generate an EKS workload cost report for `Deployment` and `StatefulSet` resources.
The command creates a JSON summary and a CSV details file.

## Safety level
- `read`

## Side effects
- Creates report files under `--output-dir`.
- Does not change Kubernetes or AWS resources.

## Command
```bash
hape eks-deployment-cost report \
  --kube-context <kube-context> \
  --aws-profile <aws-profile> \
  --output-dir <output-dir>
```

## Optional flags
- `--kube-config-file` optional kubeconfig path.
- `--aws-region` optional region code. If omitted, HAPE uses the AWS profile default region.
- `--resource-types` comma-separated values from `Deployment,StatefulSet`. Defaults to both.
- `--namespaces` comma-separated namespace names. If omitted, all namespaces are used.
- `--top-n` top workloads sorted by hourly cost in summary. Default `20`.

## Pricing model
- AWS price source: EC2 On-Demand public pricing (`pricing:GetProducts`).
- EC2 instance type is derived from running pod metadata and node labels (`node.kubernetes.io/instance-type`).
- Resource usage source: Kubernetes container `requests` only.
- Missing CPU or memory requests are treated as `0`.
- Replica normalization: `replicas_effective = replicas or 1`.
- Output includes hourly, daily, monthly (`24*30`), and yearly (`24*365`) projections.

## Output files
- `eks-deployment-cost-summary.json`
- `eks-deployment-cost-details.csv`

## Examples
```bash
hape eks-deployment-cost report \
  --kube-context dev-eu \
  --aws-profile hape \
  --aws-region eu-central-1 \
  --resource-types Deployment,StatefulSet \
  --namespaces payments,orders \
  --top-n 20 \
  --output-dir /path/to/output
```

```bash
hape eks-deployment-cost report \
  --kube-context dev-eu \
  --aws-profile hape \
  --output-dir /path/to/output
```
