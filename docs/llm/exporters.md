# HAPE Exporter Rules

Apply these rules when creating or updating Prometheus exporters in this repository.

## Hard rules
- Hard rule: Keep exporter files in `exporters/` and use `*_exporter.py`.
- Hard rule: Keep API calls in clients and business logic in services. Exporters handle refresh, payload build, and HTTP endpoints only.
- Hard rule: Define a module-level constant named `METRICS_CATALOG` for metric metadata (`name`, `type`, `description`, `labels`).
- Hard rule: Expose `GET /metrics`, `GET /metrics-catalog` (or `/catalog`), and `GET /healthz`.
- Hard rule: Keep exporter process alive on refresh failures and expose an `exporter_up` metric with value `0` on failure.
- Hard rule: Load exporter runtime config through `core/config.py`, and document every new env var in `.env.example`.

## Metrics requirements
- Keep metric names stable, snake_case, and prefixed with `hape_`.
- Emit Prometheus `HELP` and `TYPE` metadata lines for each metric family.
- Keep labels bounded to avoid unbounded cardinality.
- Escape label values before rendering exposition text.

## Documentation requirements
- Update `docs/exporters/<exporter>.md` whenever endpoint, metric, or config behavior changes.
- Update related dashboard JSON in `dashboards/` when metric schema changes.

## Validation requirements
- Run exporter locally with `python -m exporters.<module_name>`.
- Verify `/metrics`, `/metrics-catalog`, and `/healthz` responses.

## Architecture focus
- Software architecture: keep strict exporter -> service -> client responsibilities.
- System architecture: prioritize scrape reliability, bounded cardinality, and graceful degradation.
