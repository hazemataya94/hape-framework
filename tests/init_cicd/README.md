# Init CI/CD Tests

## Purpose
This suite validates standalone `init-cicd` behavior for project detection, rendering, file generation, and CLI wiring.

## Scope
- Detector tests for supported and unsupported projects.
- Renderer and writer tests for deterministic output and skip behavior.
- Scaffolder tests for generated files and warnings.
- Service and CLI tests for argument handling and typed validation failures.
- Opt-in functional test on local kind with generated artifacts.

## Prerequisites
- Use local Python environment with project dependencies installed.
- `kind` and `kubectl` are required only for functional test execution.
- No EKS cluster is required.

## Run tests
Run all init-cicd tests from repository root:
```bash
python -m pytest tests/init_cicd
```

Start local kind cluster first:
```bash
make kind-up
```

Run opt-in functional test:
```bash
HAPE_RUN_KUBE_AGENT_FUNCTIONAL_TESTS=1 python -m pytest tests/init_cicd/test_init_cicd_functional.py -s
```

## Generated artifacts
Functional test writes:
- `init-cicd-summary.txt`
- `init-cicd-result.json`

## Cleanup
- Functional test artifacts are written under pytest temp directories and cleaned automatically.
- If kind cluster was started for testing only, remove it:
```bash
kind delete cluster --name hape
```
