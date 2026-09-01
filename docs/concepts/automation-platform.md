# Automation platform

## Purpose

HAPE Framework is the execution choke point for platform and DevOps automations.

Humans and AI agents call the same CLI or API surface.

The framework does not decide when to act.

The caller decides what to run and supplies explicit flags.

## Surfaces

- CLI: `hape <domain> <command>`
- API: FastAPI endpoints with 1:1 path parity for most commands
- Exporters: Prometheus collectors that read through client adapters

## Related documentation

- [Execution model](execution-model.md)
- [Architecture](../architecture.md)
- [Tool contract](../llm/tool-contract.md)
