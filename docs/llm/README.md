# LLM Rules

## Purpose
This directory contains rule files for LLM agents.
These files define how agents should reason about safety, architecture, and coding style before making changes.

## Contents
- [safety-policy.md](safety-policy.md) - safety and scope (what is allowed / not allowed).
- [tool-contract.md](tool-contract.md) - minimal contract for agent-safe tools.
- [architecture.md](architecture.md) - architecture workflow, layering responsibilities, and guardrails.
- [coding.md](coding.md) - coding constraints, naming, typing, logging, and runtime rules.
- [kubernetes.md](kubernetes.md) - Kubernetes manifest constraints and deployment guardrails.
- [documentation.md](documentation.md) - documentation writing rules and command example conventions.
- [testing.md](testing.md) - local-first testing rules with cost-minimizing defaults.
- [exporters.md](exporters.md) - exporter-specific architecture, metrics, config, and runtime rules.
