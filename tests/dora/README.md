# DORA Test Suite

## Purpose
Validate GitLab and GitHub DORA feature logic and exporter behavior with local-first tests.

## Prerequisites
- Python dependencies installed from repository root.
- Optional local Kubernetes test environment for extended manual checks: `make kind-up`.

## Local unit and functional tests
Run all DORA tests from repository root:

```bash
python -m pytest tests/dora -q
```

Run only the functional artifact flow:

```bash
python -m pytest tests/dora/test_dora_functional.py -q
```

## Artifact outputs
The functional test generates artifacts under a temporary directory:
- `dora-summary.json`
- `dora-project-rows.csv`
- `dora-report.md`

The test prints the exact temporary artifacts directory path at runtime, even when pytest output capture is enabled.

## EKS usage
These tests do not require EKS and do not create billable cloud resources by default.

## Cleanup
No manual cleanup is required for the default test flow because artifacts are written to temporary directories managed by pytest.
