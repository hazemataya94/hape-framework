# LinkedIn Tests

## Purpose

Fixture-based tests for the LinkedIn public posts client and service.

These tests do not call LinkedIn over the network.

## Run

```
cd /Users/hazem/workspace/hape/hape-framework
source .exec-venv/bin/activate
python -m pytest tests/linkedin/ -v
```

## Artifacts

Service tests write JSON/Markdown under pytest `tmp_path` during the run.

No `kind` cluster is required.
