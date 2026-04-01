# EKS Deployment Cost Demo

## Files
- `eks-deployment-cost-summary.json`: metadata, totals, top costing workloads, and pricing context.
- `eks-deployment-cost-details.csv`: one row per workload with CPU and memory request based cost calculations.
- `prometheus-exporter-metrics.png`: Prometheus UI view of exporter metrics.
- `grafana-dashboard.png`: Grafana dashboard view for EKS deployment cost metrics.

## Screenshots
Prometheus exporter metrics view:

![Prometheus exporter metrics](./prometheus-exporter-metrics.png)

Grafana dashboard view:

![Grafana dashboard](./grafana-dashboard.png)

## Prerequisites
- Python dependencies installed for this project.
- Functional test prerequisites from `tests/eks-deployment-cost/README.md` are met.

## Steps to reproduce this demo
1) Start local kind cluster:
```bash
make kind-up
```

2) Copy AWS credentials for local secret generation:
```bash
cp ~/.aws/credentials infrastructure/kubernetes/aws-credentials/.aws-credentials
```

3) Install monitoring stack (Prometheus and Grafana):
```bash
make helmfile-sync
```

4) Create AWS credentials secret:
```bash
make kustomize-apply infrastructure/kubernetes/aws-credentials
```

5) Apply demo workloads (namespaces, Deployments, StatefulSets):
```bash
make kustomize-apply infrastructure/kubernetes/eks-deployment-cost
```

6) Deploy exporter:
```bash
make kustomize-apply infrastructure/kubernetes/exporters/eks-deployment-cost
```

7) Open Grafana and import dashboard JSON:
```bash
kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3000:80
```
Then import `dashboards/eks-deployment-cost.json` in Grafana.

8) Optional: regenerate service output demo files:
```bash
HAPE_RUN_KIND_FUNCTIONAL_TESTS=1 python -m pytest tests/eks-deployment-cost -s
```
The output files in this directory were copied from the generated test outputs.

9) Verify artifacts:
- Confirm `eks-deployment-cost-summary.json` exists and includes `metadata`, `summary`, `top_costing_workloads`, and `pricing_by_instance_type`.
- Confirm `eks-deployment-cost-details.csv` exists and includes one row per workload.
- Confirm summary totals match the expected details CSV aggregation for key cost columns.

## Cleanup
```bash
make kind-down
```

## Related documentation
- [EKS deployment cost user guide](../../docs/user/eks-deployment-cost.md)
- [EKS deployment cost service logic](../../docs/ops/eks-deployment-cost-service.md)
- [EKS deployment cost exporter](../../docs/exporters/eks-deployment-cost-exporter.md)
- [EKS deployment cost fixtures](../../docs/infra/eks-deployment-cost-fixtures.md)
- [Local Kubernetes](../../docs/infra/local-kubernetes.md)
