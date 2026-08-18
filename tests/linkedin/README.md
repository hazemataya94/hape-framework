# LinkedIn Tests

## Purpose

Fixture-based tests for the LinkedIn public posts client and service.

These tests do not call LinkedIn over the network.

## Run

```bash
python -m pytest tests/linkedin/ -v
```

## Artifacts

Service tests write JSON/Markdown under pytest `tmp_path` during the run.

No `kind` cluster is required.
