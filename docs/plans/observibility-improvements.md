# Improving observability

## Table of Contents
- [The smallest good v1](#the-smallest-good-v1)
  - [DORA](#dora)
  - [Reliability](#reliability)
  - [CI/CD](#cicd)
  - [Governance](#governance)
- [Delivery performance (DORA) metrics](#delivery-performance-dora-metrics)
  - [Source](#source)
  - [Labels](#labels)
  - [Metrics](#metrics)
- [Service reliability USE, RED, and Golden signals](#service-reliability-use-red-and-golden-signals)
  - [Source](#source-1)
  - [Metrics](#metrics-1)
- [CI/CD pipeline health](#cicd-pipeline-health)
- [Incident response metrics](#incident-response-metrics)
- [Governance and drift metrics](#governance-and-drift-metrics)
- [Change-risk and review-quality metrics](#change-risk-and-review-quality-metrics)
- [Developer productivity / developer experience](#developer-productivity--developer-experience)

## The smallest good v1
### DORA
- deployment frequency
- lead time for changes
- change fail rate
- failed deployment recovery time

### Reliability
- availability SLI
- latency SLI
- error budget remaining
- burn rate

### CI/CD
- pipeline success rate
- pipeline p95 duration
- broken default branch time
- rerun rate

### Governance
- drift count
- drift age
- policy violation count
- restore test success rate
- certificate expiry window

## Delivery performance (DORA) metrics
### Source
- GitLab Free CI pipelines and commit history
- Prometheus and Kubernetes workload signals (mapped by JSON config)
### Labels
- service
- environment
- deployment_id
- started_at
- finished_at
- result
- commit_sha    
- pipeline_id
- rollback_of
- incident_id or caused_incident
### Metrics
- hape_dora_project_info{provider,group_path,project_path,default_branch,archived}
- hape_dora_project_has_deployments{provider,group_path,project_path,environment,window}
- hape_dora_deployments_total{provider,group_path,project_path,environment,window}
- hape_dora_deployment_frequency_per_day{provider,group_path,project_path,environment,window}
- hape_dora_lead_time_seconds{provider,group_path,project_path,environment,window}
- hape_dora_failed_deployments_total{provider,group_path,project_path,environment,window}
- hape_dora_change_fail_rate_ratio{provider,group_path,project_path,environment,window}
- hape_dora_failed_deployment_recovery_time_seconds{provider,group_path,project_path,environment,window}

## Service reliability USE, RED, and Golden signals 
### Source
- https://grafana.com/blog/the-red-method-how-to-instrument-your-services/
### Metrics
- hape_http_requests_total{service,route,method,status_class}
- hape_http_request_duration_seconds_bucket{service,route,method}
- hape_http_inprogress_requests{service,route}
- hape_dependency_requests_total{service,dependency,status_class}
- hape_dependency_request_duration_seconds_bucket{service,dependency}
- hape_queue_depth{queue}
- hape_worker_busy_ratio{worker_pool}
- hape_resource_saturation_ratio{resource}

## CI/CD pipeline health
- Pipeline success rate
```bash
successful_pipelines / total_pipelines
```
- Pipeline median duration
- Pipeline p95 duration
- Queue/wait time before jobs start
```bash
job_started_at - job_created_at
```
- Deployment job success rate
- Rollback rate
```bash
rollback_deployments / total_deployments
```
- Flaky job rate
```bash
jobs that fail then pass on rerun / total jobs
```
- Rerun rate
```bash
retried_jobs / total_jobs
```
- Manual intervention rate
```bash
manual jobs executed / total pipelines
```
Broken default branch time
```bash
time the default branch stays red
```

## Incident response metrics
- MTTA: mean time to acknowledge
```bash
acknowledged_at - alert_fired_at
```
- MTTM: mean time to mitigate
```bash
mitigated_at - first_user_impact_at
```
- MTTR: mean time to resolve
```bash
resolved_at - first_user_impact_at
```
- Incident recurrence rate
```bash
repeated incidents with same fingerprint / total incidents
```
- Postmortem completion rate
```bash
incidents with postmortem completed / incidents requiring postmortem
```
- Action item closure time
```bash
action_item_done_at - postmortem_created_at
```
- Alert noise rate
```bash
non-actionable alerts / total alerts
```
- Escalation rate
```bash
incidents requiring handoff/escalation / total incidents
```

## Governance and drift metrics
- IaC drift count
```bash
number of resources whose actual config != declared config
```
- Drift age
```bash
now - first_detected_drift_at
```
- Policy violation count
```bash
for example Kyverno/OPA/security/policy failures
```
- Unreviewed production change count
```bash
direct prod changes not linked to reviewed MR
```
- Unsupported version age
```bash
now - vendor end-of-support date
```
- Certificate expiry window
```bash
days until expiry, bucketed by severity
```
- Secret rotation age
- Backup success rate
- Restore test success rate
- Restore test age
```bash
now - last_successful_restore_test_at
```
- Privileged access exception count
- Terraform/Helm drift reconciliation failure rate

## Change-risk and review-quality metrics
- MR size
```bash
changed lines / files / modules
```
- Review latency
```bash
first_review_at - ready_for_review_at
```
- Approval depth
```bash
number of approvers per MR
```
- Time from last approval to merge
- Hotfix rate
```bash
hotfix deploys / total deploys
```
- Revert rate
```bash
reverted merges / total merges
```
Rework after merge
```bash
follow-up fix MRs linked within X days
```
- Change failure probability by MR size bucket
- Change failure probability by service
- Change failure probability by time-of-day/day-of-week

## Developer productivity / developer experience
- time to first review
- time to first successful pipeline
- PR/MR pickup time
- % work blocked
- context-switch count per engineer per week
- docs update rate for infra changes
