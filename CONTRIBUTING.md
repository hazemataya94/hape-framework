# Contributing

## Purpose

This repository accepts public contributions through GitHub pull requests.

Every pull request requires personal review and explicit approval from Hazem Ataya before merge.

## License

By submitting a pull request, you license your contribution under the MIT License in `LICENSE`.

Inbound and outbound licensing are both MIT.

A separate contributor license agreement or Developer Certificate of Origin is not required.

## Prerequisites

- Python 3.9 or later.
- A local clone of https://github.com/hazemataya94/hape-framework
- Read `docs/llm/README.md` before changing HAPE Framework code.

## Local checks

Run the policy scanner and unit tests from the repository root:

```bash
python scripts/check_hape_rules.py --all
python -m pytest tests/ -q --ignore=tests/dora/test_dora_functional.py --ignore=tests/eks-deployment-cost/test_eks_deployment_cost_functional.py --ignore=tests/kube_agent/test_kube_agent_functional.py --ignore=tests/init_cicd/test_init_cicd_functional.py
```

Expected: the policy scanner and unit tests complete without failures.

## Pull request rules

- Keep changes path-bounded and reversible.
- Do not add secrets, tokens, private endpoints, or real operator defaults.
- Use dummy placeholders such as `example-org`, `/path/to/...`, and `https://vault.example.com`.
- Update matching documentation in the same change.
- Preserve CLI/API to services to clients layering.
- Do not rewrite git history.

## Review

Open a pull request against `main`.

Wait for personal review and explicit approval from Hazem Ataya.

Do not assume silence is approval.
