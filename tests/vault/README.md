# Vault tests

## Purpose

Unit tests for AppRole login and KV field retrieval through `hape vault kv-get`.

These tests use in-process fake Vault HTTP responses. They do not call Vault, PyPI, or a Kubernetes cluster.

## Prerequisites

- Python environment for this repository
- No Vault token files

## Run

```bash
python -m pytest tests/vault
```

## Cleanup

Pytest removes `tmp_path` after each test. No cluster teardown is required. `make kind-up` is not used for this suite.
