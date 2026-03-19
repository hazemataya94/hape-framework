# Exporters on Kubernetes

## Purpose
This directory contains Kubernetes deployment assets for HAPE exporters.
Use these kustomize bases to run exporters inside the local kind cluster.

## Available exporters
- `eks-deployment-cost/`
- `dora/`

## Deploy EKS deployment cost exporter
1) Create AWS credentials secret:

```bash
make kustomize-apply infrastructure/kubernetes/aws-credentials
```

2) Deploy exporter:

Apply:

```bash
make kustomize-apply infrastructure/kubernetes/exporters/eks-deployment-cost
```

Delete:

```bash
make kustomize-delete infrastructure/kubernetes/exporters/eks-deployment-cost
```

## Deploy DORA exporter
Apply:

```bash
make kustomize-apply infrastructure/kubernetes/exporters/dora
```

Delete:

```bash
make kustomize-delete infrastructure/kubernetes/exporters/dora
```

## Kubernetes access mode
The deployment uses in-cluster Kubernetes authentication through the pod service account.
No kubeconfig secret is required.

## AWS credentials
The deployment reads AWS credentials from Kubernetes Secret `hape-aws-credentials`.
Create the secret from `infrastructure/kubernetes/aws-credentials/` before deploying the exporter.

## Why load-restrictor is required
This kustomize base generates ConfigMaps directly from:
- `exporters/eks_deployment_cost_exporter.py`
- `requirements.txt`
Both files are outside this kustomization directory.
`LoadRestrictionsNone` allows this local-only file inclusion.
