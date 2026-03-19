# Infrastructure Docs

## Purpose
This section centralizes infrastructure documentation for local Kubernetes setup, Helmfile bootstrap, test fixtures, and Terraform status.

## Prerequisites
- `kind`
- `kubectl`
- `helm`
- `helmfile`
- `make`

## Sections
- [Overview](overview.md) - infrastructure scope, architecture view, and directory mapping.
- [Local Kubernetes](local-kubernetes.md) - kind cluster setup and lifecycle.
- [Helmfile Monitoring Stack](helmfile-monitoring.md) - local monitoring bootstrap via Helmfile.
- [EKS Deployment Cost Fixtures](eks-deployment-cost-fixtures.md) - Kubernetes fixtures used by functional tests.
- [Kube Agent Fixtures](kube-agent-fixtures.md) - Kubernetes fixtures used by kube-agent functional tests.
- [Terraform Status](terraform.md) - current Terraform scope and status.
- [Terraform GitLab DORA Sandbox](terraform-dora-gitlab.md) - GitLab Free sandbox setup for DORA testing.
- [Terraform GitHub DORA Sandbox](terraform-dora-github.md) - GitHub sandbox module usage for DORA testing.

## Validation steps
1. Create the local cluster:
   ```bash
   make kind-up
   ```
2. Install monitoring components:
   ```bash
   make helmfile-sync
   ```
3. Confirm cluster nodes are present:
   ```bash
   kubectl get nodes
   ```
