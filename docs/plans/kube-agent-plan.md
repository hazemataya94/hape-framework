# Kube Agent Implementation Plan

Date: 12.03.2026

## Goal
Implement `hape-kube-agent` inside `hape-framework` as a new domain for Kubernetes incident investigation.

The implementation must follow this fixed workflow:

```text
Trigger
  ↓
Evidence Collector
  ↓
Diagnostic Checks
  ↓
Incident Case
  ↓
AI Explanation (optional)
  ↓
Findings
```

The implementation must be:
- CLI-first
- read-only
- deterministic-first
- testable
- aligned with `docs/architecture.md`
- compatible with the existing HAPE layer model: CLI → Services → Clients

The implementation must not add:
- operators
- remediation actions
- tool-calling agent loops
- generic agent frameworks
- write access to Kubernetes or external systems

---

## Non-negotiable design rules

### 1. Keep AI decoupled from data collection
AI must never talk directly to Kubernetes, Prometheus, Alertmanager, Grafana, or Slack clients.
AI gets only the built `IncidentCase`.

### 2. Keep deterministic checks before AI
All diagnosis logic must first run through deterministic checks.
AI is only for:
- summarization
- hypothesis wording
- explanation
- debugging step wording
- suggested fix wording

### 3. Keep clients thin
Clients do transport and response parsing only.
Clients do not contain diagnosis logic.
Clients do not call each other.

### 4. Keep services clear
The kube-agent domain must be the orchestration layer.
Do not move business logic into CLI commands.

### 5. Keep repeated incidents in memory
The same incident should not be fully reviewed from scratch every time.
Use local SQLite storage first.

---

## Required repository fit

Target layout:

```text
hape_framework/
├── cli/
│   └── commands/
│       └── kube_agent_commands.py
│
├── services/
│   └── kube_agent/
│       ├── kube_agent_service.py
│       │
│       ├── triggers/
│       │   ├── trigger_resolver.py
│       │   ├── trigger_parser.py
│       │   └── trigger_models.py
│       │
│       ├── evidence/
│       │   ├── evidence_collector.py
│       │   ├── evidence_models.py
│       │   ├── evidence_bundle_builder.py
│       │   ├── kubernetes_evidence_collector.py
│       │   ├── prometheus_evidence_collector.py
│       │   ├── grafana_link_resolver.py
│       │   └── collectors/
│       │       ├── pod_status_collector.py
│       │       ├── pod_events_collector.py
│       │       ├── pod_logs_collector.py
│       │       ├── workload_owner_collector.py
│       │       ├── rollout_history_collector.py
│       │       ├── node_conditions_collector.py
│       │       ├── pod_metrics_collector.py
│       │       └── scheduling_failure_collector.py
│       │
│       ├── checks/
│       │   ├── diagnostic_check_engine.py
│       │   ├── diagnostic_check_models.py
│       │   ├── base_check.py
│       │   ├── registry.py
│       │   └── packs/
│       │       ├── pod_restart_checks.py
│       │       ├── pod_pending_checks.py
│       │       ├── node_condition_checks.py
│       │       ├── rollout_regression_checks.py
│       │       ├── probe_failure_checks.py
│       │       └── image_pull_checks.py
│       │
│       ├── case/
│       │   ├── incident_case_builder.py
│       │   ├── incident_case_models.py
│       │   ├── hypothesis_builder.py
│       │   └── recommendation_builder.py
│       │
│       ├── ai/
│       │   ├── ai_explainer.py
│       │   ├── ai_prompt_builder.py
│       │   ├── ai_response_parser.py
│       │   └── ai_models.py
│       │
│       ├── findings/
│       │   ├── findings_builder.py
│       │   ├── findings_models.py
│       │   ├── markdown_formatter.py
│       │   ├── json_formatter.py
│       │   └── slack_formatter.py
│       │
│       ├── memory/
│       │   ├── incident_memory_service.py
│       │   ├── incident_fingerprint.py
│       │   ├── incident_repository.py
│       │   ├── models.py
│       │   └── sqlite/
│       │       ├── sqlite_incident_repository.py
│       │       └── migrations.py
│       │
│       ├── config/
│       │   ├── kube_agent_config.py
│       │   ├── thresholds.py
│       │   └── promql_queries.py
│
├── clients/
│   ├── kubernetes_client.py
│   ├── prometheus_client.py
│   ├── alertmanager_client.py
│   ├── grafana_client.py
│   └── slack_client.py
│
└── tests/
    └── kube_agent/
```

Notes:
- Reuse existing clients when cleanly possible.
- Extend `kubernetes_client.py` and `grafana_client.py` if they already exist.
- Create `prometheus_client.py`, `alertmanager_client.py`, and `slack_client.py` only if not already present.
- Create new modules only if extending current modules would reduce cohesion.

---

## Implementation phases

## Phase 1: architecture fit and core models

### Objective
Create the minimum domain skeleton and internal data model.

### Tasks
1. Read `docs/architecture.md` and keep the existing layer rules.
2. Create `services/kube_agent/` package.
3. Add `__init__.py` files where needed.
4. Define core models first before building orchestration.

### Required models
Implement at minimum:

#### Trigger model
```python
@dataclass
class Trigger:
    kind: str  # pod | deployment | node | alert
    cluster: str
    namespace: str | None
    name: str
    source: str  # cli | alertmanager
    labels: dict[str, str]
    annotations: dict[str, str]
    metadata: dict[str, Any]
```

#### Evidence item model
```python
@dataclass
class EvidenceItem:
    key: str
    source: str
    resource_ref: str
    value: Any
    observed_at: datetime
    metadata: dict[str, Any]
```

#### Evidence bundle model
```python
@dataclass
class EvidenceBundle:
    trigger: Trigger
    items: list[EvidenceItem]
    links: dict[str, str]
```

#### Check result model
```python
@dataclass
class CheckResult:
    check_name: str
    status: str  # matched | not_matched | inconclusive
    confidence: str  # low | medium | high
    summary: str
    evidence_keys: list[str]
    details: dict[str, Any]
```

#### Incident case model
```python
@dataclass
class IncidentCase:
    case_id: str
    title: str
    summary: str
    trigger: Trigger
    evidence: EvidenceBundle
    check_results: list[CheckResult]
    likely_causes: list[str]
    hypotheses: list[str]
    recommendations: list[str]
    related_resources: list[str]
    dashboard_links: dict[str, str]
```

#### AI explanation model
```python
@dataclass
class AiExplanation:
    summary: str
    possible_root_cause: str
    reasoning: str
    debugging_steps: list[str]
    suggested_fixes: list[str]
```

#### Findings model
```python
@dataclass
class Findings:
    incident_id: str
    title: str
    summary: str
    likely_root_cause: str | None
    evidence_summary: list[str]
    debugging_steps: list[str]
    suggested_fixes: list[str]
    dashboard_links: dict[str, str]
    ai_used: bool
```

### Exit criteria
- The model layer exists.
- Names are stable.
- Type hints are clean.
- No CLI or external integration yet.

---

## Phase 2: trigger layer

### Objective
Normalize all supported investigation inputs.

### Required files
- `services/kube_agent/triggers/trigger_models.py`
- `services/kube_agent/triggers/trigger_parser.py`
- `services/kube_agent/triggers/trigger_resolver.py`

### Supported trigger kinds for v1
- pod
- deployment
- node
- alert

### Behavior
- Accept raw CLI input.
- Validate required fields.
- Normalize to one `Trigger` object.
- For alert triggers, resolve labels and annotations into internal fields.

### Example interfaces
```python
class TriggerParser:
    def parse(self, raw_trigger: dict[str, Any]) -> dict[str, Any]:
        ...

class TriggerResolver:
    def resolve(self, raw_trigger: dict[str, Any]) -> Trigger:
        ...
```

### Validation rules
- `pod` trigger requires cluster, namespace, pod name.
- `deployment` trigger requires cluster, namespace, deployment name.
- `node` trigger requires cluster, node name.
- `alert` trigger requires cluster and enough alert labels to identify the target.

### Exit criteria
- CLI input can be converted into a normalized trigger.
- Invalid trigger data returns explicit validation errors.

---

## Phase 3: client layer

### Objective
Add or extend the external clients needed for evidence collection and output delivery.

### Kubernetes client
Add or extend methods for:
- `get_pod(namespace, pod_name)`
- `list_pod_events(namespace, pod_name)`
- `get_pod_logs(namespace, pod_name, container=None, tail_lines=200)`
- `get_deployment(namespace, deployment_name)`
- `get_replicaset_history(namespace, deployment_name)`
- `get_node(node_name)`
- `list_pods_for_node(node_name)`
- `get_pod_owner(namespace, pod_name)`
- `list_related_resources(namespace, workload_name)`

### Prometheus client
Create methods for:
- `query(promql: str)`
- `query_range(promql: str, start: datetime, end: datetime, step: str)`
- helper methods only if they reduce repeated query building

### Alertmanager client
Create methods for:
- `list_alerts()`
- `get_alerts_by_labels(matchers: dict[str, str])`
- `get_alert(alert_fingerprint: str)` if practical

### Grafana client
Add or extend methods for:
- `find_dashboard_links(namespace: str | None, workload_name: str | None, node_name: str | None)`
- `build_dashboard_url_for_resource(...)`

### Slack client
Create method for:
- `send_findings(message: str, channel: str | None = None)`

### Rules
- Clients must be transport-only.
- No diagnosis logic in clients.
- Normalize responses only as needed for service use.

### Exit criteria
- Each client can be called independently.
- Failures return explicit domain errors.
- Logging is added at request boundary level.

---

## Phase 4: evidence layer

### Objective
Collect and normalize evidence from external systems.

### Required files
- `services/kube_agent/evidence/evidence_models.py`
- `services/kube_agent/evidence/evidence_bundle_builder.py`
- `services/kube_agent/evidence/evidence_collector.py`
- `services/kube_agent/evidence/kubernetes_evidence_collector.py`
- `services/kube_agent/evidence/prometheus_evidence_collector.py`
- `services/kube_agent/evidence/grafana_link_resolver.py`
- collectors under `services/kube_agent/evidence/collectors/`

### Required collectors for v1
- `pod_status_collector.py`
- `pod_events_collector.py`
- `pod_logs_collector.py`
- `workload_owner_collector.py`
- `rollout_history_collector.py`
- `node_conditions_collector.py`
- `pod_metrics_collector.py`
- `scheduling_failure_collector.py`

### Evidence collection rules
- Evidence layer collects facts only.
- No root cause conclusions.
- All results must be normalized into `EvidenceItem`.
- Use only the collectors needed for the trigger type.
- Logs must be bounded in size.
- Prometheus queries must use central templates from `config/promql_queries.py`.

### Expected evidence by trigger type

#### Pod trigger
Collect:
- pod status
- container statuses
- restart counts
- last terminated state
- pod events
- last logs tail for failing container
- owner workload
- node conditions for current node
- recent rollout context for owning workload
- Prometheus restart and resource metrics
- Grafana links

#### Deployment trigger
Collect:
- deployment spec summary
- rollout history
- related ReplicaSets
- pods for the deployment
- recent failures across owned pods
- Prometheus workload metrics
- Grafana links

#### Node trigger
Collect:
- node conditions
- pressure states
- affected pods
- recent warnings and events
- Prometheus node pressure and resource saturation metrics
- Grafana links

#### Alert trigger
Resolve target resource from alert labels first, then delegate to the relevant collectors.

### Example interface
```python
class EvidenceCollector:
    def collect(self, trigger: Trigger) -> EvidenceBundle:
        ...
```

### Exit criteria
- Evidence collection works for pod triggers first.
- Evidence is normalized and grouped in one bundle.
- Grafana links are optional and do not fail the full pipeline.

---

## Phase 5: diagnostic checks layer

### Objective
Add deterministic diagnosis logic over normalized evidence.

### Required files
- `services/kube_agent/checks/diagnostic_check_models.py`
- `services/kube_agent/checks/base_check.py`
- `services/kube_agent/checks/registry.py`
- `services/kube_agent/checks/diagnostic_check_engine.py`
- `services/kube_agent/checks/packs/*.py`

### Required engine interface
```python
class BaseDiagnosticCheck(Protocol):
    name: str

    def supports(self, trigger: Trigger, evidence: EvidenceBundle) -> bool:
        ...

    def run(self, trigger: Trigger, evidence: EvidenceBundle) -> CheckResult:
        ...

class DiagnosticCheckEngine:
    def run(self, trigger: Trigger, evidence: EvidenceBundle) -> list[CheckResult]:
        ...
```

### Initial check packs

#### pod_restart_checks.py
Required checks:
- `OomKillCheck`
- `ProbeFailureCheck`
- `EvictionCheck`
- `RecentRolloutCheck`
- `UnexpectedExitCodeCheck`

#### pod_pending_checks.py
Required checks:
- `FailedSchedulingCheck`
- `InsufficientResourceCheck`
- `TaintMismatchCheck`
- `PvcBindingCheck`
- `ImagePullFailureCheck`

#### node_condition_checks.py
Required checks:
- `MemoryPressureCheck`
- `DiskPressureCheck`
- `PidPressureCheck`
- `NodeNotReadyCheck`

#### rollout_regression_checks.py
Required checks:
- `DeploymentRevisionChangeCheck`
- `ImageChangeCheck`
- `ConfigChangeCorrelationCheck`

#### probe_failure_checks.py
Required checks:
- `ReadinessProbeFailureCheck`
- `LivenessProbeFailureCheck`

#### image_pull_checks.py
Required checks:
- `ImagePullBackOffCheck`
- `ErrImagePullCheck`

### Check behavior rules
- Checks work only on normalized evidence.
- Checks return `matched`, `not_matched`, or `inconclusive`.
- Checks include evidence keys used for the result.
- Checks do not call clients.
- Checks do not use AI.

### Initial prioritization
Implement these first, in order:
1. OOM check
2. Probe failure check
3. Failed scheduling check
4. Node pressure check
5. Recent rollout check
6. Image pull failure check

### Exit criteria
- Pod restart and pod pending diagnosis are usable.
- Check outputs are deterministic and easy to test.

---

## Phase 6: incident case layer

### Objective
Create one structured case object that combines the investigation outputs.

### Required files
- `services/kube_agent/case/incident_case_models.py`
- `services/kube_agent/case/incident_case_builder.py`
- `services/kube_agent/case/hypothesis_builder.py`
- `services/kube_agent/case/recommendation_builder.py`

### Required behavior
- Build a single `IncidentCase`.
- Convert check matches into likely causes.
- Convert incomplete results into explicit hypotheses.
- Build debugging steps from matched checks.
- Build suggested fixes from matched checks.

### Rules
- `IncidentCase` is the only input to AI explanation.
- `IncidentCase` must be understandable without reading raw API responses.
- Prefer explicit summary fields over opaque nested payloads.

### Example logic
- If `OomKillCheck` is matched with high confidence and there is no node pressure match, likely cause should include container memory exhaustion.
- If `FailedSchedulingCheck` is matched with `Insufficient memory`, likely cause should include scheduling blocked by insufficient node memory.
- If `RecentRolloutCheck` and crash checks are both matched, the case should mention rollout correlation.

### Exit criteria
- The pipeline produces a complete `IncidentCase` without AI.
- The case is enough to explain the incident in plain text.

---

## Phase 7: findings layer

### Objective
Create final user-facing outputs.

### Required files
- `services/kube_agent/findings/findings_models.py`
- `services/kube_agent/findings/findings_builder.py`
- `services/kube_agent/findings/markdown_formatter.py`
- `services/kube_agent/findings/json_formatter.py`
- `services/kube_agent/findings/slack_formatter.py`

### Required behavior
- Build `Findings` from `IncidentCase` and optional `AiExplanation`.
- Produce CLI-friendly summary.
- Produce JSON output.
- Produce Markdown output.
- Produce Slack-ready text.

### Output content
Each findings object must include:
- incident title
- summary
- likely root cause if known
- supporting evidence summary
- debugging steps
- suggested fixes
- dashboard links
- AI used flag

### Exit criteria
- Findings are readable without raw evidence dumps.
- JSON output is machine-readable.
- Markdown output is suitable for sharing.

---

## Phase 8: incident memory layer

### Objective
Persist incidents and avoid re-reviewing repeated incidents from scratch.

### Required files
- `services/kube_agent/memory/incident_memory_service.py`
- `services/kube_agent/memory/incident_fingerprint.py`
- `services/kube_agent/memory/incident_repository.py`
- `services/kube_agent/memory/models.py`
- `services/kube_agent/memory/sqlite/sqlite_incident_repository.py`
- `services/kube_agent/memory/sqlite/migrations.py`

### Storage choice
Use SQLite first.
Do not add an external database.

### Required concepts

#### Incident fingerprint
Build a stable fingerprint using:
- cluster
- namespace
- owner kind
- owner name
- incident family
- normalized likely cause signature

Example cause signatures:
- `restart:oomkilled`
- `restart:probe-failure`
- `pending:failed-scheduling`
- `node:not-ready:memory-pressure`
- `image-pull:err-image-pull`

#### Stored incident
At minimum store:
- incident id
- fingerprint
- first seen
- last seen
- occurrence count
- latest summary
- latest likely cause
- latest findings hash

#### Investigation run
At minimum store:
- run id
- incident id
- trigger summary
- evidence hash
- case hash
- AI used flag
- created at timestamp

### Memory service behavior
Required methods:
- `find_existing(trigger, incident_case=None)`
- `should_run_ai(trigger, incident_case, previous_incident)`
- `save(trigger, incident_case, findings)`

### AI skip logic
Skip repeated AI explanation when:
- fingerprint is unchanged
- evidence hash has not materially changed
- prior explanation exists and is recent enough

Run AI again when:
- fingerprint changed
- rollout revision changed
- node changed
- evidence hash changed materially
- prior explanation is stale

### Exit criteria
- Repeated incidents can be matched.
- Occurrence count increments.
- Full duplicate review can be reduced safely.

---

## Phase 9: AI explanation layer

### Objective
Add optional AI explanation on top of the incident case.

### Required files
- `services/kube_agent/ai/ai_models.py`
- `services/kube_agent/ai/ai_prompt_builder.py`
- `services/kube_agent/ai/ai_response_parser.py`
- `services/kube_agent/ai/ai_explainer.py`

### Required behavior
- AI input must be `IncidentCase` only.
- AI output must be parsed into `AiExplanation`.
- AI should never request live evidence.
- AI should not decide which evidence to collect.

### Prompt rules
The prompt must explicitly state:
- use only the provided incident case
- do not invent missing facts
- separate observed facts from hypotheses
- keep the root cause probabilistic if uncertain
- keep debugging steps concrete and ordered

### Fallback rules
- If AI fails, the investigation still succeeds.
- Findings builder must work without AI.
- AI errors must be logged clearly and surfaced as optional failure only.

### Exit criteria
- AI can explain a valid incident case.
- A failed AI call does not fail the whole investigation.

---

## Phase 10: orchestration service

### Objective
Create one top-level service that runs the complete workflow.

### Required file
- `services/kube_agent/kube_agent_service.py`

### Required interface
```python
class KubeAgentService:
    def investigate(self, raw_trigger: dict[str, Any], use_ai: bool = True) -> Findings:
        ...
```

### Required workflow
1. Resolve trigger
2. Load previous incident memory if relevant
3. Collect evidence
4. Run diagnostic checks
5. Build incident case
6. Optionally call AI explanation
7. Build findings
8. Save incident memory
9. Return findings

### Pseudocode
```python
class KubeAgentService:
    def investigate(self, raw_trigger: dict[str, Any], use_ai: bool = True) -> Findings:
        trigger = self.trigger_resolver.resolve(raw_trigger)

        previous_incident = self.incident_memory_service.find_existing(trigger)

        evidence = self.evidence_collector.collect(trigger)
        check_results = self.diagnostic_check_engine.run(trigger, evidence)

        incident_case = self.incident_case_builder.build(
            trigger=trigger,
            evidence=evidence,
            check_results=check_results,
        )

        ai_explanation = None
        if use_ai and self.incident_memory_service.should_run_ai(
            trigger=trigger,
            incident_case=incident_case,
            previous_incident=previous_incident,
        ):
            ai_explanation = self.ai_explainer.explain(incident_case)

        findings = self.findings_builder.build(
            incident_case=incident_case,
            ai_explanation=ai_explanation,
        )

        self.incident_memory_service.save(
            trigger=trigger,
            incident_case=incident_case,
            findings=findings,
        )

        return findings
```

### Exit criteria
- One service runs the whole pipeline.
- Every layer can be unit-tested independently.
- The orchestration code remains short and readable.

---

## Phase 11: CLI integration

### Objective
Expose kube-agent through the HAPE CLI.

### Required file
- `cli/commands/kube_agent_commands.py`

### Initial commands
Implement these first:

```bash
hape kube-agent investigate pod --kube-context <ctx> --namespace <ns> --pod <pod>
hape kube-agent investigate deployment --kube-context <ctx> --namespace <ns> --deployment <deployment>
hape kube-agent investigate node --kube-context <ctx> --node <node>
hape kube-agent investigate alert --kube-context <ctx> --alertname <alertname>
hape kube-agent incidents list
hape kube-agent incidents show --incident-id <id>
```

### CLI rules
- Commands parse args only.
- Commands call `KubeAgentService`.
- Do not put evidence or diagnosis logic in commands.
- Add output format flags where useful, for example `--output json|markdown|text`.
- Add `--use-ai` as explicit opt-in if current HAPE defaults prefer predictability.

### Exit criteria
- Pod investigation works from the CLI.
- Incident list and show commands work from SQLite memory.

---

## Phase 12: configuration

### Objective
Add explicit kube-agent configuration without hiding settings in command code.

### Required files
- `services/kube_agent/config/kube_agent_config.py`
- `services/kube_agent/config/thresholds.py`
- `services/kube_agent/config/promql_queries.py`

### Required config categories
- restart thresholds
- time windows
- default log tail size
- AI enabled default
- SQLite database path
- Prometheus query templates
- Slack output settings

### Rules
- Keep thresholds in config, not inside checks.
- Keep PromQL templates centralized.
- Keep AI provider configuration outside the evidence and check layers.

---

## Phase 13: testing

### Objective
Make the feature stable and regression-safe.

### Required test areas

#### Unit tests
- trigger parsing and validation
- each evidence collector
- each diagnostic check
- incident case builder
- findings builder
- memory fingerprinting and dedup logic
- AI prompt builder and parser

#### Integration tests
- full `investigate pod` with mocked clients
- repeated incident memory behavior
- AI optional path and no-AI path

### Specific required tests

#### Trigger tests
- valid pod trigger
- invalid pod trigger missing namespace
- valid alert trigger with label mapping

#### Evidence tests
- pod status evidence normalization
- pod events evidence normalization
- logs truncation behavior
- Prometheus metric normalization

#### Check tests
- OOMKilled case returns matched
- readiness probe failures return matched
- failed scheduling due to memory returns matched
- no supporting evidence returns inconclusive or not matched as expected

#### Case tests
- matched checks become likely causes
- mixed evidence produces hypotheses
- dashboard links are preserved

#### Memory tests
- same incident creates same fingerprint
- changed cause creates new fingerprint
- occurrence count increments
- AI skip logic behaves as designed

#### CLI tests
- command parses flags correctly
- output selection works
- service is called with expected raw trigger payload

### Exit criteria
- Pod investigation path has solid coverage.
- Repeated incident handling is tested.

---

## Initial implementation priority

Build in this exact order:

1. Core models
2. Trigger layer
3. Kubernetes client extension
4. Prometheus client
5. Evidence layer for pod trigger
6. Pod restart checks
7. Pod pending checks
8. Incident case builder
9. Findings builder
10. KubeAgentService
11. CLI command for `investigate pod`
12. Incident memory with SQLite
13. Alertmanager trigger support
14. Node and deployment trigger support
15. AI explanation layer
16. Slack output

Reason:
- pod investigation gives the fastest useful path
- pod restart and pending incidents cover a large part of common Kubernetes incidents
- memory should come before broadening trigger coverage
- AI comes after deterministic investigation is already useful

---

## Minimum viable first release

The first useful release must support:
- `hape kube-agent investigate pod`
- Kubernetes evidence collection for a pod incident
- Prometheus metrics lookup for pod restart and resource symptoms
- deterministic checks for:
  - OOM
  - probe failures
  - failed scheduling
  - image pull failures
  - node pressure
  - recent rollout correlation
- incident case building
- findings output in text and JSON
- SQLite incident memory

Optional in the same release if easy:
- Markdown formatting
- Grafana links

Not required for the first release:
- Slack delivery
- AI explanation
- Alertmanager-triggered investigation
- deployment and node CLI flows

---

## Explicit anti-goals

Do not implement these in this project phase:
- operator pattern
- controllers or CRDs
- event-driven cluster-side automation
- autonomous remediation
- open-ended agent tool selection
- generic graph database
- vector database
- multi-tenant storage backend

---

## Expected coding style

- Use short, explicit method names.
- Prefer dataclasses or typed models over raw dict passing once inside the domain.
- Keep orchestration code thin.
- Keep checks small and focused.
- Do not hide control flow in decorators or meta-frameworks.
- Add docstrings where they clarify behavior.
- Keep logging at boundaries and decision points.
- Prefer explicit failure messages.

---

## Deliverables expected from the implementing agent

The implementation agent should produce:
1. New kube-agent package structure
2. Core typed models
3. Required clients and client extensions
4. Evidence collection for pod investigations
5. Deterministic check engine and first check packs
6. Incident case builder
7. Findings builder and formatters
8. SQLite-backed incident memory
9. KubeAgentService orchestration
10. CLI integration
11. Unit and integration tests
12. Any needed docs updates for command usage if implementation adds user-visible commands

---

## Final instruction to the implementing agent

Implement `hape-kube-agent` as a bounded HAPE domain for Kubernetes incident investigation.

Do not redesign HAPE into a generic agent platform.
Do not add operator behavior.
Do not let AI drive evidence collection.
Make pod investigation useful first.
Keep the architecture readable for a non-expert engineer.
