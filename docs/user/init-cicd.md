# Init CI/CD

## Purpose
Use `hape init-cicd` to scaffold Kubernetes deployment manifests and CI build workflow files for supported React projects.

## Command
```bash
hape init-cicd --project-path /path/to/react/project --deployment-type kubernetes
```

## Required flags
- `--project-path`: path to the application repository root.
- `--deployment-type`: deployment target type. v1 supports only `kubernetes`.

## Safety and side effects
- Command writes local files in the target project directory.
- Existing files are skipped and are not overwritten in v1.
- Generated manifests are namespace-neutral.
- Generated deployment manifest does not set CPU under `resources.limits`.
- Generated workflow is build-only and does not push images or deploy.

## Generated files
- `deployments/deployment.yaml`
- `deployments/service.yaml`
- `deployments/serviceaccount.yaml`
- `deployments/hpa.yaml`
- `deployments/kustomization.yaml`
- `Dockerfile`
- `.dockerignore`
- `.github/workflows/deploy.yaml`

## Existing file behavior
- If `deployments/` exists, manifest generation is skipped and root/workflow files are still generated when missing.
- If `Dockerfile` exists, it is skipped with a warning.
- If `.dockerignore` exists, it is skipped.
- If `.github/workflows/deploy.yaml` exists, it is skipped with a warning.

## Validation steps
1. Run:
```bash
hape init-cicd --project-path /path/to/react/project --deployment-type kubernetes
```
2. Confirm command output contains `Created`, `Skipped`, and `Warnings`.
3. Confirm deployment manifest contains no `namespace` field.
4. Confirm deployment manifest has no CPU under `resources.limits`.
5. Confirm workflow has no `docker push` or deploy steps.

## Future direction
Future versions can support more deployment types such as `aws-serversless`.
