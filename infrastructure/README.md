# Infrastructure

## Purpose
This directory contains local infrastructure setup assets for HAPE development and testing.
It includes local Kubernetes setup on `kind` and Terraform assets for GitLab and GitHub DORA sandbox provisioning.

## Directory layout
- `kubernetes/`: local Kubernetes cluster setup, Helmfile definitions, and bootstrap manifests.
- `terraform/`: Terraform modules and environment stacks.

## Current scope
- Create and manage a local `kind` cluster for development and functional tests.
- Install local cluster tools with Helmfile.

## Future scope
- Expand Terraform coverage for additional domains beyond DORA sandbox usage.
