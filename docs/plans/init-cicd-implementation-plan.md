# Init CI/CD Implementation Plan

Date: 2026-03-23

## Objective
Implement a standalone `init-cicd` feature that scaffolds Kubernetes deployment files and CI files for application repositories.

Version 1 must:
- support only React frontend projects
- support React projects built with Vite, Create React App, and generic `npm run build`
- create Kubernetes manifests under a new `deployments/` folder
- create a `Dockerfile`
- create a GitHub Actions workflow
- keep generated manifests namespace-neutral
- not create ingress, secrets, externalsecrets, configmaps, or database resources
- not deploy to Kubernetes
- not push images to a registry
- fit the existing HAPE architecture and existing repo structure

The user-facing command must be:

```bash
hape init-cicd --project-path /path/to/react/project --deployment-type kubernetes
```

---

## Final v1 behavior

When the command runs against a supported React project:

1. validate the project path
2. validate deployment type
3. detect the project type as React
4. detect the build flavor:
   - Vite
   - CRA
   - generic React with `npm run build`
5. create `deployments/` if it does not already exist
6. generate these Kubernetes files inside `deployments/`:
   - `deployment.yaml`
   - `service.yaml`
   - `serviceaccount.yaml`
   - `hpa.yaml`
   - `kustomization.yaml`
7. generate project root files if missing:
   - `Dockerfile`
   - `.dockerignore`
8. generate GitHub workflow if missing:
   - `.github/workflows/deploy.yaml`
9. print a clear summary of:
   - created files
   - skipped files
   - warnings

If `deployments/` already exists:
- print a message that it already exists
- do not overwrite the folder contents
- stop generation for deployment manifests
- continue generation for missing project root files (`Dockerfile`, `.dockerignore`) and workflow file (`.github/workflows/deploy.yaml`)

If `Dockerfile` already exists:
- skip it
- print a warning
- continue

If `.github/workflows/deploy.yaml` already exists:
- skip it
- print a warning
- continue

If `.dockerignore` already exists:
- skip it
- continue

The command must be safe and conservative.
Do not overwrite existing files in v1.
Do not add `--force` in v1 unless implementation is trivial.

---

## Hard constraints
These are not optional.

1. Keep the implementation inside the existing repo. Do not create a separate templates repository in v1.
2. Keep templates local to `hape-framework`.
3. Do not rename `services/kube_agent/` to `services/kube-agent/`.
4. Keep CLI thin. Business logic must live in services.
5. Keep investigation and incident logic separate from cost analysis and separate from init-cicd logic.
6. Generated manifests must be namespace-neutral.
7. Do not generate ingress in v1.
8. Do not generate secrets, configmaps, externalsecrets, databases, or environment-specific overlays in v1.
9. GitHub workflow must build only.
10. GitHub workflow must assume Docker Hub naming for the image reference shape, but must not push.
11. GitHub workflow must not deploy to Kubernetes.
12. Support Vite, CRA, and generic React build projects.
13. Existing files must be skipped, not overwritten.
14. Keep architecture aligned with `docs/architecture.md` and the existing CLI → Services → Clients layering.
15. Do not set CPU values under `resources.limits` in generated Kubernetes manifests.
16. `InitCicdService` must use `HapeValidationError` and `HapeExternalError` with `code`, human message, and minimal non-sensitive context.
17. All kube-agent services must follow the same `HapeValidationError` and `HapeExternalError` error contract.
18. `init-cicd` must be a standalone top-level CLI command, not a kube-agent subcommand.
19. v1 must require `--deployment-type kubernetes` and reject unsupported deployment types.

---

## Architecture alignment

This implementation must follow the existing HAPE layering.

- CLI parses arguments and calls service methods only.
- Services contain project detection, template rendering, file generation, and result reporting.
- Clients are not needed for v1 because this feature is local file generation only.
- Template files are static assets, not logic containers.
- Detection logic must be deterministic.
- File writing logic must be centralized so skip and idempotency behavior stays consistent.

Do not put generation logic into:
- CLI commands
- template files
- utility modules with no domain boundary

---

## Required repository fit

Target layout:

```text
hape_framework/
├── cli/
│   └── commands/
│       ├── kube_agent_commands.py
│       └── init_cicd_commands.py
│
├── services/
│   ├── kube_agent/
│       ├── kube_agent_service.py
│       │
│       ├── investigation/
│       │   ├── investigation_service.py
│       │   ├── incidents_service.py
│       │   ├── triggers/
│       │   ├── evidence/
│       │   ├── checks/
│       │   ├── case/
│       │   ├── ai/
│       │   ├── findings/
│       │   └── memory/
│       │
│       ├── cost/
│       │   ├── cost_analysis_service.py
│       │   ├── cost_models.py
│       │   └── ...
│       │
│   └── init_cicd/
│       ├── __init__.py
│       ├── init_cicd_service.py
│       ├── models.py
│       │
│       ├── detector/
│       │   ├── __init__.py
│       │   ├── project_detector.py
│       │   └── reactjs_detector.py
│       │
│       ├── scaffolders/
│       │   ├── __init__.py
│       │   ├── base_scaffolder.py
│       │   └── reactjs_scaffolder.py
│       │
│       ├── renderer/
│       │   ├── __init__.py
│       │   └── template_renderer.py
│       │
│       ├── writer/
│       │   ├── __init__.py
│       │   └── file_writer.py
│       │
│       └── templates/
│           └── reactjs/
│               ├── deployment.yaml.tpl
│               ├── service.yaml.tpl
│               ├── serviceaccount.yaml.tpl
│               ├── hpa.yaml.tpl
│               ├── kustomization.yaml.tpl
│               ├── Dockerfile.tpl
│               ├── .dockerignore.tpl
│               └── github-deploy.yaml.tpl
│
└── tests/
    └── init_cicd/
        ├── test_project_detector.py
        ├── test_reactjs_detector.py
        ├── test_template_renderer.py
        ├── test_file_writer.py
        ├── test_reactjs_scaffolder.py
        ├── test_init_cicd_cli.py
        └── fixtures/
            ├── react_vite/
            ├── react_cra/
            ├── react_generic/
            └── non_react/
```

Notes:
- `kube_agent_service.py` may remain as a thin compatibility facade.
- Existing kube-agent investigation modules should move under `investigation/` only if the move is low-risk and testable.
- If a large move would create excessive churn, phase the restructuring with compatibility imports.

---

## Service boundary plan

### 1. Investigation domain
Contains:
- `investigate`
- `incidents list`
- `incidents show`
- existing trigger, evidence, checks, case, AI, findings, and memory modules

### 2. Cost domain
Contains:
- `cost-analyze`
- cost-specific models and formatting

### 3. Init CI/CD domain
Contains:
- project detection
- template selection
- template rendering
- file creation
- idempotent skip logic
- result summary

This domain is standalone because `init-cicd` is local project scaffolding and should not be coupled to kube-agent command grouping.

---

## CLI design

The CLI must support:

```bash
hape init-cicd --project-path /path/to/project --deployment-type kubernetes
```

Recommended future-safe optional flags, only if low complexity:

```bash
--framework reactjs
--dry-run
```

But in v1, the minimum required flag is only:

```bash
--project-path
--deployment-type kubernetes
```

### CLI behavior rules
- validate that the path exists
- validate that the path is a directory
- validate deployment type
- call only the `InitCicdService`
- print deterministic output
- exit non-zero on unsupported or invalid projects

### CLI output example
```text
Init CI/CD
Project: /workspace/my-react-app
Deployment type: kubernetes
Framework: reactjs
Build flavor: vite

Created:
- deployments/deployment.yaml
- deployments/service.yaml
- deployments/serviceaccount.yaml
- deployments/hpa.yaml
- deployments/kustomization.yaml
- Dockerfile
- .dockerignore
- .github/workflows/deploy.yaml

Skipped:
- none

Warnings:
- none
```

---

## Detection design

Implement detection in two layers.

### ProjectDetector
Responsibilities:
- load `package.json`
- decide whether the repo is supported
- delegate to the framework-specific detector

### ReactJsDetector
Responsibilities:
- confirm React project support
- detect build flavor
- compute build output directory
- derive normalized app name

### React support rules
A project is supported when:
- `package.json` exists
- `dependencies` or `devDependencies` contains `react`
- `dependencies` or `devDependencies` contains `react-dom`

### Build flavor detection rules
Use these rules in order:

1. Vite React
   - `vite` exists in dependencies or devDependencies
   - build output directory: `dist`

2. CRA React
   - `react-scripts` exists in dependencies or devDependencies
   - build output directory: `build`

3. Generic React build
   - `scripts.build` exists in `package.json`
   - build output directory default: `build`
   - add a warning that generic projects may need Dockerfile adjustment if their output directory differs

If React is not detected, fail with a clear unsupported-project message.

### App name normalization
Use `package.json.name` as the base name.
Normalize into a Kubernetes-safe name:
- lowercase only
- replace spaces and invalid characters with `-`
- trim leading or trailing `-`
- keep DNS-1123 compatible output

If normalized name is empty, fail clearly.

---

## Rendering model

Do not introduce a heavy templating engine unless there is already one in the repo.
For v1, use a small placeholder renderer.

### Recommended placeholder style
Use simple placeholders such as:

```text
{{ app_name }}
{{ image }}
{{ container_port }}
{{ build_output_dir }}
```

### Required render context
At minimum:
- `app_name`
- `image_repository`
- `image_tag`
- `container_port`
- `service_port`
- `replicas`
- `min_replicas`
- `max_replicas`
- `cpu_request`
- `memory_request`
- `memory_limit`
- `build_output_dir`
- `workflow_name`

### Recommended defaults
- `image_repository`: `docker.io/CHANGE_ME/{{ app_name }}`
- `image_tag`: `latest`
- `container_port`: `80`
- `service_port`: `80`
- `replicas`: `2`
- `min_replicas`: `2`
- `max_replicas`: `5`
- `cpu_request`: `100m`
- `memory_request`: `128Mi`
- `memory_limit`: `512Mi`
- `workflow_name`: `deploy`

These defaults are suitable for a simple static frontend and are easy to change later.

---

## File generation behavior

Centralize all file writing in `file_writer.py`.

### Required file writer behaviors
1. Create parent directories when needed.
2. Skip existing files.
3. Return structured information about created and skipped files.
4. Never silently overwrite files in v1.
5. Support writing text files with predictable UTF-8 encoding.

### Required result model
Implement at minimum:

```python
from dataclasses import dataclass, field

@dataclass
class InitCicdResult:
    project_path: str
    framework: str
    build_flavor: str
    created_files: list[str] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
```

### Recommended project model
```python
from dataclasses import dataclass

@dataclass
class DetectedProject:
    framework: str
    build_flavor: str
    app_name: str
    project_path: str
    build_output_dir: str
```

---

## Template content requirements

### 1. `deployment.yaml`
Must include:
- `apps/v1`
- `Deployment`
- label set based on `app_name`
- selector labels matching pod template labels
- `replicas: 2`
- `serviceAccountName`
- container image placeholder
- container port `80`
- readiness probe on `/`
- liveness probe on `/`
- resource requests
- memory limit
- no CPU value under `resources.limits`

Recommended deployment shape:
- one container only
- no volumes
- no env vars in v1
- no namespace field

### 2. `service.yaml`
Must include:
- `v1`
- `Service`
- `type: ClusterIP`
- service port `80`
- target port `80`
- selector matching deployment labels
- no namespace field

### 3. `serviceaccount.yaml`
Must include:
- `v1`
- `ServiceAccount`
- app-specific name
- no annotations in v1
- no namespace field

### 4. `hpa.yaml`
Must include:
- `autoscaling/v2`
- `HorizontalPodAutoscaler`
- target reference to the generated deployment
- `minReplicas: 2`
- `maxReplicas: 5`
- CPU utilization target
- memory utilization target
- no namespace field

Recommended targets:
- CPU average utilization: `70`
- memory average utilization: `80`

### 5. `kustomization.yaml`
Must include:
- list of generated resources
- no namespace field
- no image transforms in v1 unless trivial and tested

The simplest valid v1 is a static resource list.

### 6. `Dockerfile`
Use a multi-stage Dockerfile.

Build stage:
- Node LTS image
- `WORKDIR /app`
- copy package manifest files first
- run dependency install
- copy source
- run `npm run build`

Runtime stage:
- `nginx:alpine`
- copy build output to nginx html directory
- expose port `80`
- default nginx command

Build output directory depends on detection:
- Vite → `dist`
- CRA → `build`
- generic React → `build` by default

### 7. `.dockerignore`
Must include common exclusions such as:
- `node_modules`
- `.git`
- `deployments`
- `.github`
- `dist`
- `build`
- local env files when safe to ignore

### 8. `.github/workflows/deploy.yaml`
Despite the name, v1 behavior is build only.

The workflow must:
- run on push to `main`
- optionally run on pull request if trivial
- check out code
- set up Docker build capability
- build the image locally
- not log in to Docker Hub
- not push the image
- not deploy to Kubernetes

Recommended image tag shape:
- `docker.io/CHANGE_ME/{{ app_name }}:${{ github.sha }}`

Recommended workflow steps:
1. checkout
2. build image
3. print built image tag

Do not include:
- registry login
- docker push
- kubectl apply
- kubeconfig setup
- Helm
- ArgoCD
- Flux

---

## Suggested workflow content direction

Example intent only:

```yaml
name: Build

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build image
        run: |
          docker build -t docker.io/CHANGE_ME/my-app:${GITHUB_SHA} .
      - name: Print image reference
        run: echo "Built docker.io/CHANGE_ME/my-app:${GITHUB_SHA}"
```

The final workflow can be slightly more polished, but it must stay build-only.

---

## Restructuring plan for kube-agent

The current kube-agent command surface mixes investigation, incidents, and cost analysis under one service area.
This implementation should use the init-cicd work as the point to make service boundaries clearer.

### Target outcome
- `investigate` and `incidents` live in an investigation domain
- `cost-analyze` lives in a cost domain
- `init-cicd` lives in an init_cicd domain

### Recommended low-risk migration strategy

#### Step 1
Create new packages:
- `services/kube_agent/investigation/`
- `services/kube_agent/cost/`
- `services/init_cicd/`

#### Step 2
Move or wrap existing investigation modules under `investigation/`.
If direct moves create too much churn, create thin forwarding modules first.

#### Step 3
Move cost-specific logic under `cost/`.

#### Step 4
Add `init_cicd/` as a new fully isolated package.

#### Step 5
Keep `services/kube_agent/kube_agent_service.py` as a thin compatibility facade that delegates to:
- `InvestigationService`
- `IncidentsService`
- `CostAnalysisService`
- `InitCicdService`

This reduces breakage and keeps the CLI stable during migration.

---

## Implementation phases

## Phase 1: service split and scaffolding skeleton

### Objective
Create the new package boundaries without breaking current kube-agent behavior.

### Tasks
1. Create `services/init_cicd/` package skeleton.
2. Create `services/kube_agent/investigation/` package skeleton.
3. Create `services/kube_agent/cost/` package skeleton.
4. Add service classes for each domain.
5. Make `kube_agent_service.py` a thin delegating facade if needed.
6. Keep imports stable where possible.
7. Introduce and standardize kube-agent service error contract usage with `HapeValidationError` and `HapeExternalError`.

### Deliverables
- new package structure exists
- current commands still import cleanly
- no change in behavior yet for existing features
- kube-agent service error contract alignment is in place or tracked with explicit low-risk compatibility steps

---

## Phase 2: CLI command and service contract

### Objective
Add the `init-cicd` CLI command and wire it to a dedicated service.

### Tasks
1. Add `cli/commands/init_cicd_commands.py`.
2. Add `--project-path` and `--deployment-type` arguments.
3. Register `init-cicd` as a top-level command in `cli/main.py`.
4. Call `InitCicdService` only.
5. Return deterministic exit codes and summary output.

### Deliverables
- `hape init-cicd --project-path ... --deployment-type kubernetes` is callable
- CLI validation errors are clear

---

## Phase 3: project detection

### Objective
Detect supported React projects and compute generation context.

### Tasks
1. Implement `ProjectDetector`.
2. Implement `ReactJsDetector`.
3. Load and parse `package.json` safely.
4. Detect React dependency presence.
5. Detect Vite, CRA, or generic build flavor.
6. Normalize app name.
7. Build `DetectedProject` result.

### Deliverables
- supported and unsupported projects are identified correctly
- build output directory is determined predictably

---

## Phase 4: template rendering and file generation

### Objective
Generate the required files safely and deterministically.

### Tasks
1. Add all v1 template files under `templates/reactjs/`.
2. Implement `TemplateRenderer`.
3. Implement `FileWriter`.
4. Implement `ReactJsScaffolder`.
5. Create `deployments/` folder when missing.
6. Generate manifests.
7. Generate `Dockerfile`, `.dockerignore`, and GitHub workflow.
8. Track created and skipped files in `InitCicdResult`.

### Deliverables
- valid files generated for supported React projects
- skip behavior works correctly

---

## Phase 5: tests

### Objective
Make the feature safe to refactor and predictable across project types.

### Tasks
1. Add fixture repositories for:
   - Vite React
   - CRA React
   - generic React build
   - unsupported non-React project
2. Add detector tests.
3. Add renderer tests.
4. Add file writer tests.
5. Add scaffolder tests.
6. Add CLI tests.
7. Add snapshot-like content assertions for generated files.
8. Add kind-backed functional tests for `init-cicd` flow.
9. Ensure functional tests generate real output artifacts and preserve them for demo derivation.

### Required test coverage
At minimum, cover:
- valid Vite project
- valid CRA project
- valid generic React project
- missing `package.json`
- non-React project
- existing `deployments/`
- existing `Dockerfile`
- existing `.github/workflows/deploy.yaml`
- app name normalization

### Deliverables
- test suite for v1 init-cicd behavior
- no regressions to existing kube-agent commands
- kind-backed functional tests run locally with deterministic generated artifacts

---

## Phase 6: documentation

### Objective
Document the new feature and the new service boundaries.

### Tasks
1. Add or update `docs/user/init-cicd.md` with standalone command usage.
2. Update `docs/user/kube-agent.md` to remove `init-cicd` from kube-agent surface.
3. Add or update `docs/ops/init-cicd-service.md` for standalone service flow.
4. Update `docs/ops/kube-agent-service.md` to remove init-cicd ownership.
5. Keep docs concise and aligned with current repo style.

### Deliverables
- user docs show the new command
- ops docs reflect the restructured service domains

---

## Error handling requirements

The implementation must fail clearly.

### Required user-facing error cases
1. project path does not exist
2. project path is not a directory
3. `package.json` missing
4. `package.json` invalid JSON
5. unsupported project type
6. app name normalization results in empty value
7. template file missing inside the tool itself
8. file system write failure
9. unsupported deployment type

### Required behavior
- return clear messages
- do not partially overwrite files
- when possible, keep already-created files and report exactly what happened
- use `HapeValidationError` for bad input and validation failures
- use `HapeExternalError` for external dependency or system interaction failures
- include error `code`, human-readable message, and minimal non-sensitive context
- apply this contract in `InitCicdService` and align all kube-agent services to this contract

---

## Validation steps

### Manual validation 1: Vite React
1. create or use a Vite React app fixture
2. run:
```bash
hape init-cicd --project-path /path/to/vite-react-app --deployment-type kubernetes
```
3. confirm these files exist:
```text
deployments/deployment.yaml
deployments/service.yaml
deployments/serviceaccount.yaml
deployments/hpa.yaml
deployments/kustomization.yaml
Dockerfile
.dockerignore
.github/workflows/deploy.yaml
```
4. confirm generated manifests contain no namespace field
5. confirm Dockerfile copies `dist/`
6. confirm workflow builds only and does not push or deploy
7. confirm generated deployment manifest does not set CPU under `resources.limits`

### Manual validation 2: CRA React
1. run command against CRA app
2. confirm Dockerfile copies `build/`
3. confirm manifests and workflow are generated

### Manual validation 3: Generic React build
1. run command against generic React app with `npm run build`
2. confirm generation succeeds
3. confirm warning is printed about possible output directory adjustment

### Manual validation 4: Existing files
1. pre-create `Dockerfile`
2. pre-create `.github/workflows/deploy.yaml`
3. run command
4. confirm both are skipped and warnings are printed
5. confirm other missing files are still created

### Manual validation 5: Existing deployments folder
1. pre-create `deployments/`
2. run command
3. confirm command prints that deployments already exist
4. confirm no deployment manifests are overwritten
5. confirm missing `Dockerfile`, `.dockerignore`, and `.github/workflows/deploy.yaml` are still generated

### Functional validation on kind (required)
1. start local kind cluster:
```bash
make kind-up
```
2. run functional test suite for init-cicd using fixture projects
3. confirm tests generate real output artifacts (for example generated manifests and summary output captures)
4. derive demo documentation artifacts from generated functional test artifacts
5. clean up local test resources after completion

---

## Acceptance criteria

The feature is complete for v1 when all of the following are true:

1. `hape init-cicd --project-path ... --deployment-type kubernetes` exists and runs.
2. Vite React projects are detected and scaffolded.
3. CRA React projects are detected and scaffolded.
4. Generic React projects with `npm run build` are detected and scaffolded.
5. `deployments/` is created only when missing.
6. `deployment.yaml`, `service.yaml`, `serviceaccount.yaml`, `hpa.yaml`, and `kustomization.yaml` are generated.
7. `Dockerfile` is generated when missing.
8. `.dockerignore` is generated when missing.
9. `.github/workflows/deploy.yaml` is generated when missing.
10. Existing `Dockerfile` and workflow file are skipped with warnings.
11. Generated manifests are namespace-neutral.
12. No ingress, secrets, configmaps, externalsecrets, or database resources are generated.
13. Generated GitHub workflow builds only.
14. Generated GitHub workflow does not push.
15. Generated GitHub workflow does not deploy.
16. Generated manifests do not set CPU under `resources.limits`.
17. Init CI/CD lives outside kube-agent as a standalone command and service package.
18. Kube-agent services use `HapeValidationError` and `HapeExternalError` with `code`, message, and minimal context.
19. Tests cover supported, unsupported, and skip scenarios.
20. Functional test flow runs on local kind and generates real artifacts used by demos.
21. User and ops docs are updated.

---

## Out of scope for v1

Do not implement these now:
- backend framework support
- PHP support
- Python support
- Golang support
- JavaScript generic non-React support
- multi-environment overlays
- dev/staging/prod overlays
- ingress generation
- configmaps
- secrets
- externalsecrets
- registry push
- Kubernetes deployment from CI
- Helm chart generation
- ArgoCD or Flux integration
- template repository split into a separate repo
- interactive prompts
- runtime dependency installation checks

---

## Recommended future v2 directions

After v1 is stable, the next reasonable extensions are:
1. `--force` overwrite behavior
2. `--dry-run`
3. support for backend frameworks
4. support for multiple registries
5. support for overlays and environments
6. optional ingress generation
7. optional image tag replacement in `kustomization.yaml`
8. optional GitOps-friendly workflow generation
9. shared framework template contract across React, Node, Python, PHP, and Go
10. additional deployment types (for example `aws-serversless`)

---

## Implementation note for Codex

Prefer small commits in this order:
1. service/package split
2. CLI wiring
3. detector
4. renderer and file writer
5. React scaffolder and templates
6. tests
7. docs

Do not start with templates first.
Detection and file-writing rules should be stable before template content is finalized.

For any newly created Python module, include an `if __name__ == "__main__":` block that exercises all public functions.
