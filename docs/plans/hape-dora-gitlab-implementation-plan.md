# HAPE / DORA / GitLab / Implementation Plan

Date: 2026-03-16

## Objective
Implement a GitLab-based DORA metrics feature in HAPE Framework that:
- works on GitLab Free
- does not depend on GitLab Premium or Ultimate features
- does not depend on GitLab deployment records, environments, or built-in DORA analytics
- is designed so the core logic can later be reused for GitHub
- uses CI deploy job success as the deployment event source
- uses Git commit history for lead time
- uses Prometheus and Kubernetes signals for change fail rate and failed deployment recovery time
- exposes Prometheus metrics through a new exporter
- provides Grafana dashboards named:
  - `HAPE / DORA / GitLab / Overview`
  - `HAPE / DORA / GitLab / Group`
  - `HAPE / DORA / GitLab / Project`
- includes Terraform files to create a GitLab.com Free sandbox for testing

---

## Hard constraints
These are not optional.

1. Do not use GitLab paid features.
2. Do not use GitLab DORA APIs.
3. Do not use GitLab deployment records or environment records.
4. Deployment frequency must be based only on successful CI deploy jobs.
5. Deployment identification rules must come from a JSON configuration file.
6. Kubernetes mapping rules must come from a JSON configuration file.
7. Include all configured projects in overview and group views, including projects with zero deploys.
8. In dashboards, show lowest non-zero values where that makes sense.
9. In dashboards, show separate tables for no deploy data and no change data.
10. Keep architecture aligned with `docs/architecture.md` and `docs/llm/exporters.md`.

---

## Architecture alignment
This implementation must follow the existing HAPE layering.

- CLI parses input and calls services only.
- Services contain business logic.
- Clients contain raw external API access.
- Exporter handles refresh loop, metric exposition, and HTTP endpoints only.
- Configuration is loaded through `core/config.py`.
- Metric names must start with `hape_`.
- Labels must stay bounded.

Do not put business logic into:
- CLI commands
- clients
- dashboards
- Kubernetes manifests

---

## Final v1 scope
Implement these four metrics only.

1. Deployment frequency
2. Lead time for changes
3. Change fail rate
4. Failed deployment recovery time

Out of scope for v1:
- deployment rework rate
- rollback rate
- MR-based lead time
- GitLab environments
- GitLab deployment records
- GitLab paid APIs
- GitHub support
- auto-discovery of Kubernetes mappings

---

## Metric definitions

### 1) Deployment frequency
Definition:
- count successful deploy jobs in CI/CD within the selected rolling window

Source of truth:
- GitLab pipeline jobs only

Important:
- do not require Kubernetes rollout success for this metric
- the deploy job name may differ per project, so detection must come from JSON config

Recommended exported metrics:
- `hape_dora_deployments_total{provider,group_path,project_path,environment,window}`
- `hape_dora_deployment_frequency_per_day{provider,group_path,project_path,environment,window}`
- `hape_dora_project_has_deployments{provider,group_path,project_path,environment,window}`

### 2) Lead time for changes
Definition:
- for each successful deployment event, find the commits newly included since the previous successful deployment event for the same project and environment
- compute `deployment_finished_at - commit_committed_date` for each included commit
- aggregate as median lead time for the selected window

Source of truth:
- Git commit history + successful deploy job events

Notes:
- use commit history, not merge requests, so the logic remains portable to GitHub later
- if a project has no successful deployments or no included commits, it has no change data

Recommended exported metric:
- `hape_dora_lead_time_seconds{provider,group_path,project_path,environment,window}`

### 3) Change fail rate
Definition:
- percentage of successful deployment events that are followed by a deployment-related failure within a configured detection window

Formula:
- `failed_deployments / total_successful_deployments`

Source of truth:
- successful deploy events from CI/CD
- failure detection from Prometheus and Kubernetes

Recommended exported metrics:
- `hape_dora_failed_deployments_total{provider,group_path,project_path,environment,window}`
- `hape_dora_change_fail_rate_ratio{provider,group_path,project_path,environment,window}`

### 4) Failed deployment recovery time
Definition:
- time from the first detected post-deploy failure signal to the first stable recovery point

Source of truth:
- Prometheus and Kubernetes signals mapped to the deployed workload

Notes:
- this is not GitLab incident recovery time
- this is operational recovery after a deployment caused instability

Recommended exported metrics:
- `hape_dora_failed_deployment_recovery_time_seconds{provider,group_path,project_path,environment,window}`
- `hape_dora_open_failed_deployments_total{provider,group_path,project_path,environment,window}`

---

## Data sources

### GitLab
Use GitLab Free-compatible APIs only.

Needed data:
- groups and projects
- pipelines
- jobs inside pipelines
- commits
- default branch

Do not use:
- built-in DORA analytics
- deployment APIs as a required source
- environment APIs as a required source

### Git
Needed data:
- commit SHA for each deployment event
- commit committed date
- commit range between successive deployments

### Kubernetes and Prometheus
Needed data:
- explicit project-to-workload mapping from JSON
- health and failure signals for mapped workloads

---

## Configuration design
Two JSON files are required.

### 1) Git identification config
Create:
- `config/dora/git-rules.json`

This file defines how deploy jobs are identified.

#### Required behavior
- support defaults
- support per-group overrides
- support per-project overrides
- production refs must be explicit in every project config
- deploy job names must be configurable
- deploy stage names may also be configurable

#### Recommended schema
```json
{
  "version": 1,
  "defaults": {
    "provider": "gitlab",
    "environment": "production",
    "successful_job_statuses": ["success"],
    "deploy_job_names": ["deploy"],
    "deploy_job_name_regex": [],
    "deploy_stages": ["deploy"],
    "failure_detection_minutes": 60,
    "recovery_timeout_minutes": 240,
    "recovery_stability_minutes": 10
  },
  "groups": [
    {
      "group_path": "example/platform",
      "defaults": {
        "deploy_job_names": ["deploy", "release"],
        "deploy_stages": ["deploy", "release"]
      }
    }
  ],
  "projects": [
    {
      "project_path": "example/platform/service-a",
      "default_branch": "main",
      "refs": ["main"],
      "environment": "production",
      "deploy_job_names": ["deploy-prod"],
      "deploy_job_name_regex": ["^deploy-prod$"],
      "deploy_stages": ["deploy"],
      "failure_detection_minutes": 60,
      "recovery_timeout_minutes": 240,
      "recovery_stability_minutes": 10
    }
  ]
}
```

#### Resolution order
When determining rules for a project, resolve in this order:
1. defaults
2. matching group defaults
3. project overrides

Project values win over group values. Group values win over global defaults.

### 2) Kubernetes mapping config
Create:
- `config/dora/kubernetes-mappings.json`

This file defines how each project maps to Kubernetes workloads and Prometheus labels.

#### Required behavior
- explicit mapping only in v1
- no name inference
- allow one project to map to one or more workloads
- allow label matchers needed for Prometheus queries

#### Recommended schema
```json
{
  "version": 1,
  "defaults": {
    "provider": "gitlab",
    "cluster": "kind-hape",
    "workload_kind": "Deployment"
  },
  "projects": [
    {
      "project_path": "example/platform/service-a",
      "cluster": "kind-hape",
      "namespace": "payments",
      "workloads": [
        {
          "kind": "Deployment",
          "name": "service-a",
          "prometheus_label_matchers": {
            "namespace": "payments",
            "deployment": "service-a"
          }
        }
      ]
    }
  ]
}
```

---

## Internal domain model
Create simple typed internal models or dataclasses for normalized data.

Recommended models:
- `DoraProjectRule`
- `DoraKubernetesMapping`
- `DoraDeploymentEvent`
- `DoraFailureEvent`
- `DoraProjectWindowMetrics`

### Normalized deployment event shape
```json
{
  "provider": "gitlab",
  "group_path": "example/platform",
  "project_path": "example/platform/service-a",
  "project_id": 123,
  "default_branch": "main",
  "environment": "production",
  "pipeline_id": 456,
  "job_id": 789,
  "job_name": "deploy-prod",
  "stage": "deploy",
  "ref": "main",
  "sha": "abc123",
  "status": "success",
  "started_at": "2026-03-16T10:00:00Z",
  "finished_at": "2026-03-16T10:04:00Z"
}
```

The rest of the DORA logic should use normalized models, not raw GitLab JSON.

---

## File and module plan

### Extend existing client
Update:
- `clients/gitlab_client.py`

Add methods:
- `get_project(project_id: int) -> dict`
- `get_group_projects(group_id: int, include_subgroups: bool = True, archived: bool = False) -> list[dict]`
- `get_project_pipelines(project_id: int, updated_after: str, updated_before: str, ref: str | None = None, status: str | None = None) -> list[dict]`
- `get_pipeline_jobs(project_id: int, pipeline_id: int) -> list[dict]`
- `get_project_commits(project_id: int, ref_name: str, since: str | None = None, until: str | None = None) -> list[dict]`

Implementation notes:
- reuse paginated request pattern
- centralize HTTP GET handling if needed
- raise clear errors on non-200 responses
- do not mix business logic into the client

### New services
Create:
- `services/dora_config_service.py`
- `services/dora_gitlab_provider_service.py`
- `services/dora_deployment_event_service.py`
- `services/dora_lead_time_service.py`
- `services/dora_failure_service.py`
- `services/dora_aggregation_service.py`
- `services/dora_service.py`

### Service responsibilities

#### `services/dora_config_service.py`
Responsibilities:
- load `git-rules.json`
- load `kubernetes-mappings.json`
- validate required keys
- resolve effective per-project deploy rules using defaults + group + project overrides
- resolve per-project Kubernetes mappings

Do not:
- call GitLab
- call Prometheus
- compute metrics

#### `services/dora_gitlab_provider_service.py`
Responsibilities:
- fetch projects for configured groups
- include projects with zero deployments
- fetch pipelines/jobs/commits as needed
- return normalized raw provider data to higher services

Do not:
- compute DORA metrics
- render Prometheus metrics

#### `services/dora_deployment_event_service.py`
Responsibilities:
- identify successful deploy jobs based on resolved deploy rules
- convert matching jobs into normalized deployment events
- sort deployment events chronologically per project/environment
- keep only successful deploy jobs

Detection rules:
- job status must be in `successful_job_statuses`
- ref must be in explicit project `refs`
- job name must match configured job names or regex
- stage may optionally be required if configured

#### `services/dora_lead_time_service.py`
Responsibilities:
- for each deployment event, determine previous successful deployment event for same project/environment
- compute included commit set between previous SHA and current SHA
- calculate lead time per commit
- aggregate median lead time per window

Edge cases:
- first known deployment has no previous deployment baseline; mark as no change data
- same SHA deployed twice should not create duplicate change set
- if no commits are found in range, mark as no change data

#### `services/dora_failure_service.py`
Responsibilities:
- for each successful deployment event, inspect mapped workloads in the post-deploy window
- detect failure onset
- detect recovery point
- return failed deployment records and recovery durations

Failure detection inputs:
- Prometheus queries
- Kubernetes mapping config
- optionally Kubernetes client reads when needed for workload status validation

Failure signals to support in v1:
- unavailable replicas after deployment
- rollout not progressing / observed generation lag
- pod restart increase after deployment
- pods not ready
- CrashLoopBackOff or failed container state

Recovery definition in v1:
- mapped workloads return to healthy state
- desired replicas equal available replicas
- no failing pods for mapped workload
- healthy state remains stable for `recovery_stability_minutes`

#### `services/dora_aggregation_service.py`
Responsibilities:
- compute rolling windows: `7d`, `30d`, `90d`
- aggregate global overview, group view, and project view
- include projects with zero deploys
- separate no deploy data and no change data buckets

#### `services/dora_service.py`
Responsibilities:
- top-level orchestration for the exporter and future CLI use
- call config service, provider service, deployment event service, lead time service, failure service, and aggregation service
- return a single structured snapshot for metric exposition

---

## Exporter plan
Create:
- `exporters/dora_exporter.py`

Follow existing exporter rules from `docs/llm/exporters.md`.

### Required endpoints
- `GET /metrics`
- `GET /metrics-catalog`
- `GET /healthz`

### Required behavior
- expose module-level `METRICS_CATALOG`
- continue serving even if refresh fails
- expose exporter up metric
- use `core/config.py` for runtime configuration

### Suggested runtime config keys
Add to `core/config.py` and `.env.example`:
- `HAPE_DORA_EXPORTER_HOST`
- `HAPE_DORA_EXPORTER_PORT`
- `HAPE_DORA_EXPORTER_REFRESH_SECONDS`
- `HAPE_DORA_GITLAB_GROUP_IDS`
- `HAPE_DORA_GIT_RULES_PATH`
- `HAPE_DORA_KUBERNETES_MAPPINGS_PATH`
- `HAPE_DORA_PROMETHEUS_URL`
- `HAPE_DORA_KUBE_CONTEXT`

Notes:
- keep naming aligned with existing config style
- if preferred, reuse shared exporter host/port keys and add only DORA-specific keys where needed
- document every new key

---

## Prometheus metrics plan
Keep labels bounded. Do not use commit SHA, pipeline ID, or job ID as metric labels.

### Core metrics
- `hape_dora_project_info{provider,group_path,project_path,default_branch,archived}` = 1
- `hape_dora_project_has_deployments{provider,group_path,project_path,environment,window}`
- `hape_dora_deployments_total{provider,group_path,project_path,environment,window}`
- `hape_dora_deployment_frequency_per_day{provider,group_path,project_path,environment,window}`
- `hape_dora_lead_time_seconds{provider,group_path,project_path,environment,window}`
- `hape_dora_failed_deployments_total{provider,group_path,project_path,environment,window}`
- `hape_dora_change_fail_rate_ratio{provider,group_path,project_path,environment,window}`
- `hape_dora_failed_deployment_recovery_time_seconds{provider,group_path,project_path,environment,window}`
- `hape_dora_open_failed_deployments_total{provider,group_path,project_path,environment,window}`

### Exporter health metrics
- `hape_dora_exporter_up`
- `hape_dora_exporter_last_refresh_timestamp_seconds`
- `hape_dora_projects_discovered_total{provider}`
- `hape_dora_projects_scanned_total{provider}`

### Windows
Use rolling windows:
- `7d`
- `30d`
- `90d`

---

## Dashboard plan
Create three dashboards under `dashboards/`.

### Files
- `dashboards/hape-dora-gitlab-overview.json`
- `dashboards/hape-dora-gitlab-group.json`
- `dashboards/hape-dora-gitlab-project.json`

### Titles
- `HAPE / DORA / GitLab / Overview`
- `HAPE / DORA / GitLab / Group`
- `HAPE / DORA / GitLab / Project`

### Dashboard rules
- include all configured projects
- where “lowest” is shown, use lowest non-zero where applicable
- include separate “no deploy data” and “no change data” tables
- do not let zeros dominate bottom-10 rankings

### Overview dashboard
Purpose:
- all configured projects across all configured groups

Panels:
- total projects
- projects with deploy data
- projects with no deploy data
- total deployments
- median lead time
- average change fail rate
- median recovery time

Tables:
- top 10 highest deployment frequency
- top 10 lowest non-zero deployment frequency
- top 10 no deploy data
- top 10 highest lead time
- top 10 lowest non-zero lead time
- top 10 no change data
- top 10 highest change fail rate
- top 10 lowest non-zero change fail rate
- top 10 highest recovery time
- top 10 lowest non-zero recovery time

Variables:
- window
- environment
- cluster

### Group dashboard
Purpose:
- one selected GitLab group

Variables:
- group
- window
- environment
- cluster

Panels and tables:
- same structure as overview, but scoped to selected group

### Project dashboard
Purpose:
- one selected project

Variables:
- group
- project
- window
- environment
- cluster

Panels:
- deployments over time
- deployment frequency
- lead time trend
- failed deployments count
- change fail rate trend
- recovery time trend
- recent deployment events summary

---

## Kubernetes and Prometheus query plan
The failure service must use explicit project mappings from `kubernetes-mappings.json`.

### v1 failure signals
Start with these signals only.

1. Deployment unavailable replicas
2. Rollout not progressing or observed generation lag
3. Pod restart increase after deployment
4. Pods not ready
5. CrashLoopBackOff or failed container state

### v1 recovery rules
Recovery occurs when all mapped workloads satisfy:
- desired replicas == available replicas
- no failing pods for mapped workload
- healthy state remains stable for configured stability window

### Implementation note
Prometheus query templates should be centralized inside the failure service or a small helper module. Do not spread query strings across exporter code.

---

## Terraform sandbox plan
The repository currently treats Terraform as a placeholder. This feature should add a first real Terraform stack for GitLab.com Free testing.

### Directories to create
- `infrastructure/terraform/modules/gitlab_group/`
- `infrastructure/terraform/modules/gitlab_project/`
- `infrastructure/terraform/modules/gitlab_repository_files/`
- `infrastructure/terraform/envs/dora-demo-gitlab/`

### Sandbox goal
Create a GitLab.com Free sandbox with:
- one group
- optional subgroup
- three to five test projects
- repository bootstrap files
- sample `.gitlab-ci.yml`
- small sample app or placeholder deploy script
- sample Kubernetes manifests

### Important boundary
Terraform should create the sandbox structure.
Terraform should not be used to generate realistic deployment history across time.

### Seed script for test history
Create a separate script:
- `scripts/dora_seed_gitlab.py`

Responsibilities:
- create commits
- trigger pipelines
- create successful deploy-job events
- optionally apply broken and fixed manifests to a local kind cluster

This keeps Terraform simple and deterministic.

---

## Kubernetes deployment assets
Create:
- `infrastructure/kubernetes/exporters/dora/deployment.yaml`
- `infrastructure/kubernetes/exporters/dora/service.yaml`
- `infrastructure/kubernetes/exporters/dora/servicemonitor.yaml`
- `infrastructure/kubernetes/exporters/dora/kustomization.yaml`

Add RBAC only if the exporter needs Kubernetes API reads beyond Prometheus.
If Prometheus alone is enough for v1 failure detection, keep RBAC minimal or absent.

---

## CLI plan
CLI is optional for exporter runtime, but useful for debugging and local verification.

Recommended additions:
- extend `cli/commands/gitlab_commands.py` only if needed for debug commands
- otherwise create `cli/commands/dora_commands.py`

Possible debug commands:
- `dora validate-config`
- `dora list-projects`
- `dora list-deployments`
- `dora compute-project --project-path ...`

Do not put business logic in CLI commands.

---

## Documentation plan
Create or update these docs.

### New docs
- `docs/user/dora.md`
- `docs/ops/exporters/dora-exporter.md`
- `docs/ops/dora-gitlab.md`
- `docs/infra/terraform-dora-gitlab.md`

### Existing docs to update
- `docs/plans/observibility-improvements.md`
  - replace old DORA assumptions that depended on GitLab features or high-cardinality labels
- `docs/user/config.md`
  - document new config keys and JSON file paths
- `.env.example`
  - add new exporter/config keys

### Documentation content requirements
Document:
- required JSON files
- how rule resolution works
- how to run exporter locally
- how to validate metrics endpoints
- dashboard names and expected panels
- Terraform sandbox usage

---

## Testing plan
Implement tests in layers.

### Unit tests
Add tests for:
- config loading and override resolution
- deployment job matching
- deployment event normalization
- lead time calculation across commit ranges
- failure detection from mocked Prometheus responses
- recovery point detection
- aggregation for overview/group/project views

Suggested test paths:
- `tests/dora/test_dora_config_service.py`
- `tests/dora/test_dora_deployment_event_service.py`
- `tests/dora/test_dora_lead_time_service.py`
- `tests/dora/test_dora_failure_service.py`
- `tests/dora/test_dora_aggregation_service.py`

### Exporter tests
Add tests for:
- `/metrics`
- `/metrics-catalog`
- `/healthz`
- exporter-up behavior on refresh failure

Suggested test path:
- `tests/dora/test_dora_exporter.py`

### Functional tests
Add functional tests using fixtures for:
- multiple projects in one group
- projects with deploy data
- projects with zero deploy data
- projects with no change data
- failed deployment followed by recovery

Suggested test path:
- `tests/dora/test_dora_functional.py`

### Sandbox validation
Use the Terraform sandbox + seed script for manual end-to-end validation.

---

## Implementation sequence
Implement in this order.

### Phase 1: configuration
1. create `config/dora/git-rules.json` example
2. create `config/dora/kubernetes-mappings.json` example
3. implement `dora_config_service.py`
4. add config validation tests

### Phase 2: GitLab provider support
1. extend `clients/gitlab_client.py`
2. implement `dora_gitlab_provider_service.py`
3. add provider tests

### Phase 3: deployment event detection
1. implement `dora_deployment_event_service.py`
2. verify explicit refs handling
3. verify deploy job name and regex matching
4. add tests

### Phase 4: lead time
1. implement `dora_lead_time_service.py`
2. support commit-range-based lead time
3. add tests for first deployment, repeated SHA, and no-change cases

### Phase 5: failure and recovery
1. implement `dora_failure_service.py`
2. add Prometheus query helpers
3. add tests for failed deployment and recovery windows

### Phase 6: aggregation
1. implement `dora_aggregation_service.py`
2. compute 7d, 30d, 90d windows
3. include no-deploy and no-change buckets
4. add tests

### Phase 7: top-level service and exporter
1. implement `dora_service.py`
2. implement `exporters/dora_exporter.py`
3. add metrics catalog
4. add exporter tests

### Phase 8: dashboards
1. add overview dashboard JSON
2. add group dashboard JSON
3. add project dashboard JSON
4. validate panel names and variables

### Phase 9: Terraform sandbox
1. add Terraform modules and env stack
2. add repository bootstrap files
3. add seed script
4. document usage

### Phase 10: docs
1. add user docs
2. add ops docs
3. update config docs
4. update observability plan doc

---

## Acceptance criteria
The work is complete when all of the following are true.

### Core behavior
- HAPE can scan configured GitLab groups on GitLab Free.
- HAPE includes all configured projects in the aggregated output.
- HAPE can detect successful deploy jobs based on JSON rules.
- HAPE computes deployment frequency from successful deploy jobs only.
- HAPE computes lead time from commit history between successive successful deployments.
- HAPE computes change fail rate from post-deploy failure detection.
- HAPE computes failed deployment recovery time from failure onset to stable recovery.

### Configuration
- git rules are loaded from `config/dora/git-rules.json`
- Kubernetes mappings are loaded from `config/dora/kubernetes-mappings.json`
- defaults + group overrides + project overrides work correctly
- project refs are explicit in project config

### Exporter
- exporter starts locally
- `/metrics` works
- `/metrics-catalog` works
- `/healthz` works
- exporter remains alive on refresh failure
- metric labels remain bounded

### Dashboards
- three dashboard JSON files exist
- dashboard titles use the GitLab path in the title
- overview shows no deploy data table
- overview shows no change data table
- bottom tables use lowest non-zero where applicable

### Terraform sandbox
- Terraform can create a GitLab.com Free sandbox structure
- seed script can create realistic enough history to test the exporter and dashboards

### Tests and docs
- unit tests exist for the core services
- exporter tests exist
- docs exist for user, ops, and Terraform sandbox usage

---

## Non-goals and guardrails
Do not do these during v1 unless explicitly requested later.

- do not add GitHub support yet
- do not auto-discover workload mappings
- do not model deployment success from Kubernetes rollout success
- do not model lead time from merge request merge time
- do not expose high-cardinality labels
- do not couple core DORA logic to GitLab-only concepts

---

## Recommended first implementation choices
To reduce ambiguity and speed up implementation, use these defaults in the first working version.

1. Windows: `7d`, `30d`, `90d`
2. Deploy detection: match configured job names first, then regex, optionally filter by configured stages
3. Lead time aggregation: median
4. Change fail rate detection window: 60 minutes by default
5. Recovery timeout: 240 minutes by default
6. Recovery stability window: 10 minutes by default
7. Overview aggregation should include all configured projects, even with zero data
8. Use explicit project mappings only

---

## Deliverables summary
By the end of the implementation, the repository should contain:

### Config
- `config/dora/git-rules.json`
- `config/dora/kubernetes-mappings.json`

### Code
- updated `clients/gitlab_client.py`
- `services/dora_config_service.py`
- `services/dora_gitlab_provider_service.py`
- `services/dora_deployment_event_service.py`
- `services/dora_lead_time_service.py`
- `services/dora_failure_service.py`
- `services/dora_aggregation_service.py`
- `services/dora_service.py`
- `exporters/dora_exporter.py`

### Dashboards
- `dashboards/hape-dora-gitlab-overview.json`
- `dashboards/hape-dora-gitlab-group.json`
- `dashboards/hape-dora-gitlab-project.json`

### Infra
- `infrastructure/kubernetes/exporters/dora/...`
- `infrastructure/terraform/modules/...`
- `infrastructure/terraform/envs/dora-demo-gitlab/...`
- `scripts/dora_seed_gitlab.py`

### Tests
- `tests/dora/...`

### Docs
- `docs/user/dora.md`
- `docs/ops/exporters/dora-exporter.md`
- `docs/ops/dora-gitlab.md`
- `docs/infra/terraform-dora-gitlab.md`

