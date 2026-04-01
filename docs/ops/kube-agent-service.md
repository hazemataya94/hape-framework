# Kube Agent Service Logic

## Purpose
Document kube-agent service boundaries and runtime behavior for investigation, incidents, and cost analysis.

## Service and module locations
- Compatibility facade: `services/kube_agent/kube_agent_service.py`.
- Investigation domain:
  - `services/kube_agent/investigation/investigation_service.py`
  - `services/kube_agent/investigation/incidents_service.py`
  - `services/kube_agent/investigation/investigation_runtime.py`
  - `services/kube_agent/investigation/triggers/`
  - `services/kube_agent/investigation/evidence/`
  - `services/kube_agent/investigation/checks/`
  - `services/kube_agent/investigation/case/`
  - `services/kube_agent/investigation/findings/`
  - `services/kube_agent/investigation/memory/`
- Cost domain:
  - `services/kube_agent/cost/cost_analysis_service.py`
- AI layer remains: `services/kube_agent/ai/`
- CLI commands: `cli/commands/kube_agent_commands.py`

## Investigation runtime flow
```mermaid
flowchart TD
  A[CLI investigate command] --> B[InvestigationService]
  B --> C[InvestigationRuntime]
  C --> D[TriggerResolver]
  D --> E[EvidenceCollector]
  E --> F[DiagnosticCheckEngine]
  F --> G[IncidentCaseBuilder]
  G --> H[IncidentMemoryService find_existing]
  H --> I[AI decision]
  I --> J[AiExplainer optional]
  G --> K[FindingsBuilder]
  J --> K
  K --> L[IncidentMemoryService save]
  L --> M[CLI output text json markdown slack]
```

## Layer boundaries
- CLI parses arguments and calls domain services only.
- `KubeAgentService` is a compatibility facade and delegates to investigation and incidents services.
- `InvestigationService` orchestrates the runtime and wraps failures with typed HAPE errors.
- `CostAnalysisService` builds cost trigger input and delegates to investigation flow.
- Clients perform transport operations only.
- Deterministic checks consume normalized evidence only.
- AI explanation consumes `IncidentCase` only.
- Memory service stores fingerprints and runs and does not collect evidence.

## Error contract
- Services raise typed HAPE errors.
- Validation and input failures use `HapeValidationError`.
- External and system interaction failures use `HapeExternalError`.
- Errors include stable code, user-facing message, and minimal non-sensitive context.

## Trigger handling
- Supported kinds are `pod`, `deployment`, `node`, `alert`, and `cost`.
- Trigger parsing normalizes names and maps kind-specific fields.
- Trigger resolver enforces required fields by kind.

## Evidence collection behavior
- Kubernetes evidence includes pod status, events, logs, owner, rollout context, node conditions, and scheduling failures.
- Prometheus evidence includes pod, node, alert, and cost-focused query outputs.
- Alertmanager evidence adds matched alerts for alert triggers.
- Grafana default dashboard collector selects high-value kube-prometheus-stack dashboards with resource query variables.
- Grafana link resolver adds additional dashboard links into the evidence bundle.

## Deterministic checks behavior
- Check engine runs registry checks and returns `matched`, `not_matched`, or `inconclusive`.
- Check packs include restart, pending, node conditions, rollout regression, probe failures, image pull checks, and cost anomaly checks.
- Incident case builder derives likely causes, hypotheses, recommendations, and related resources from check results.

## AI explanation behavior
- AI is optional and runs after deterministic checks.
- AI input is the bounded incident case.
- AI rerun logic uses incident fingerprint and staleness window.

## Incident memory behavior
- SQLite schema stores incidents and investigation runs.
- Fingerprint includes cluster, namespace, kind, resource name, and normalized cause signature.
- Repeated incidents increment `occurrence_count`.
- `incidents list` and `incidents show` read from SQLite memory.

## Operational validation
1. Run a pod investigation:
```bash
hape kube-agent investigate pod --kube-context demo --namespace payments --pod api --output markdown --use-ai false
```
2. Confirm output includes summary, likely root cause, and debugging steps.
3. Run incident list:
```bash
hape kube-agent incidents list --output text
```
4. Confirm latest incident appears.
5. Repeat the same investigate command.
6. Confirm occurrence count increases in `incidents show`.
7. Run cost analysis:
```bash
hape kube-agent cost-analyze --kube-context demo --namespace payments --deployment api --historical-offset 1h --output markdown --use-ai false
```
8. Confirm output includes exporter health, hourly cost context, and threshold-based anomaly statuses.
9. Run namespace-wide cost increase analysis:
```bash
hape kube-agent cost-analyze --kube-context demo --namespace payments --all-workloads --historical-offset 1h --output markdown --use-ai false
```
10. Confirm findings include workloads that increased compared to one hour ago.
## Test references
- Kube-agent unit and integration tests: `tests/kube_agent/`.
- Run all kube-agent tests:
```bash
python -m pytest tests/kube_agent
```

## Related documentation
- [Kube Agent (User Guide)](../user/kube-agent.md)
- [Kube Agent Architecture](../architectures/kube_agent_architecture.md)
- [Kube Agent Fixtures](../infra/kube-agent-fixtures.md)
- [Helmfile Monitoring Stack](../infra/helmfile-monitoring.md)
