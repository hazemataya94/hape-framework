# Kube Agent

## Purpose
Use `hape kube-agent` to investigate Kubernetes incidents with a deterministic-first workflow.
Use optional AI explanation only after deterministic checks complete.
Read architecture details in `kube_agent_architecture.md`.

## Prerequisites
- A valid kube context name for `--kube-context`.
- Reachable APIs for Kubernetes, Prometheus, Alertmanager, and Grafana.
- Local writable path for SQLite incident memory.

## Safety and side effects
- `investigate` is read-only for Kubernetes and monitoring systems.
- `investigate` writes local incident memory to SQLite.
- `incidents list` and `incidents show` read local SQLite memory only.
- When Prometheus URL is local (`localhost` or `127.0.0.1`), kube-agent attempts to create a Kubernetes port-forward to Prometheus before querying metrics.
- When Grafana URL is local (`localhost` or `127.0.0.1`), kube-agent attempts to create a Kubernetes port-forward to Grafana before resolving dashboard links.

## Environment configuration
Set these values in `.env` or your shell environment.

- `HAPE_KUBE_AGENT_PROMETHEUS_URL`: Prometheus API base URL.
- `HAPE_KUBE_AGENT_GRAFANA_URL`: Grafana API base URL.
- `HAPE_KUBE_AGENT_GRAFANA_TOKEN`: Optional Grafana API token.
- `HAPE_KUBE_AGENT_GRAFANA_USERNAME`: Optional Grafana basic auth username.
- `HAPE_KUBE_AGENT_GRAFANA_PASSWORD`: Optional Grafana basic auth password.
- `HAPE_KUBE_AGENT_ALERTMANAGER_URL`: Alertmanager API base URL.
- `HAPE_KUBE_AGENT_SQLITE_PATH`: Local SQLite file path for incident memory.
- `HAPE_KUBE_AGENT_AI_ENABLED`: Default AI behavior for investigations.
- `HAPE_KUBE_AGENT_AI_STALE_HOURS`: Hours before AI explanation is considered stale.
- `HAPE_KUBE_AGENT_RESTART_THRESHOLD`: Restart threshold for deterministic checks.
- `HAPE_KUBE_AGENT_POD_LOG_TAIL_LINES`: Default pod log tail size.
- `HAPE_KUBE_AGENT_LOOKBACK_MINUTES`: Default evidence lookback window.
- `HAPE_KUBE_AGENT_SLACK_CHANNEL`: Default Slack channel for Slack-formatted output.
- `HAPE_KUBE_AGENT_COST_TOTAL_HOURLY_USD_THRESHOLD`: Threshold for total hourly cost anomaly checks.
- `HAPE_KUBE_AGENT_COST_WORKLOAD_HOURLY_USD_THRESHOLD`: Threshold for deployment hourly cost anomaly checks.
- `HAPE_KUBE_AGENT_COST_INCREASE_RATIO_THRESHOLD`: Threshold for current versus historical hourly increase ratio.
- `HAPE_KUBE_AGENT_COST_TOP_WORKLOADS_LIMIT`: Number of top workloads collected for cost context evidence.

## Investigate commands

### Pod
```bash
hape kube-agent investigate pod --kube-context demo --namespace payments --pod api --output markdown --use-ai false
```

### Deployment
```bash
hape kube-agent investigate deployment --kube-context demo --namespace payments --deployment api --output text --use-ai false
```

### Node
```bash
hape kube-agent investigate node --kube-context demo --node ip-10-0-0-1 --output json --use-ai false
```

### Alert
```bash
hape kube-agent investigate alert --kube-context demo --alertname KubePodCrashLooping --namespace payments --pod api --output markdown --use-ai true
```

### Cost Analyze
```bash
hape kube-agent cost-analyze --kube-context demo --namespace payments --deployment api --historical-offset 1h --output markdown --use-ai false
```

Analyze all namespace workloads and detect hourly increases:
```bash
hape kube-agent cost-analyze --kube-context demo --namespace payments --all-workloads --historical-offset 1h --output markdown --use-ai false
```

## Incident memory commands
```bash
hape kube-agent incidents list --output text
hape kube-agent incidents show --incident-id <incident-id> --output json
```

## Output formats
- `text`: prints findings summary.
- `json`: prints machine-readable findings or incident memory records.
- `markdown`: prints shareable incident report text.
- `slack`: prints Slack-ready incident summary text.

## Validation steps
1. Run one `investigate` command with a known pod incident.
2. Confirm command output contains summary and likely root cause fields.
3. Run `hape kube-agent incidents list --output text`.
4. Confirm a new incident record appears with an incrementing occurrence count on repeated runs.
5. Run `hape kube-agent cost-analyze --kube-context demo --namespace payments --deployment api`.
6. Confirm output includes cost context and threshold-based anomaly checks.
