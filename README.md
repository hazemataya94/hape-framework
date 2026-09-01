<img src="https://raw.githubusercontent.com/hazemataya94/hape-framework/refs/heads/main/docs/logo.jpg" width="100%" alt="HAPE Framework">

# HAPE Framework

HAPE Framework is a Python CLI and FastAPI toolkit for platform and DevOps automation.

Use it to run explicit, auditable commands against systems such as GitHub, GitLab, Kubernetes, Vault, AWS ECR, Jira, and Confluence.

## Start here

1. [Install HAPE](docs/getting-started/installation.md)
2. [Five-minute quick start](docs/getting-started/five-minute-quickstart.md)
3. [Configure one integration](docs/getting-started/configuration.md)
4. [Understand command safety](docs/getting-started/safety-basics.md)
5. [Add HAPE rules to your AI IDE](docs/ai-ide/README.md)

Public technical documentation: [https://framework.hapesolutions.com](https://framework.hapesolutions.com)

Source repository: [https://github.com/hazemataya94/hape-framework](https://github.com/hazemataya94/hape-framework)

## What it automates

- Repository bootstrap and GitHub or GitLab operations.
- DORA metric computation and exporter workflows.
- Kubernetes incident investigation.
- EKS deployment cost reporting.
- Vault AppRole login and KV field retrieval.
- Jira, Confluence, CSV, and Markdown conversions.
- FastAPI endpoints with 1:1 CLI path parity for most commands.

## Install

```bash
python -m pip install hape
hape --version
hape --help
```

Expected: the installed version prints, then the command list prints.

## Safe first command

```bash
hape config show
```

Safety level: `read`.

Side effects: none.

Sensitive values are redacted unless you pass `--reveal-secrets`.

## Documentation

- [Documentation portal](docs/README.md)
- [CLI reference](docs/cli/README.md)
- [API reference](docs/api/README.md)
- [Architecture](docs/architecture.md)
- [AI IDE integration](docs/ai-ide/README.md)

## License

MIT License.

Copyright (c) 2026 Hazem Ataya.

See [LICENSE](LICENSE).

## Contributions

Public pull requests are accepted.

Every pull request requires personal review and explicit approval from Hazem Ataya.

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

Report vulnerabilities privately to `hazem.ataya@hapesolutions.com`.

See [SECURITY.md](SECURITY.md).

## HAPE Solutions

- [HAPE Solutions](https://hapesolutions.com) is the company website.
- [HAPE Vibes](https://vibes.hapesolutions.com) is a separate product for service creation and deployment workflows.

## Demos

- [Demos directory](demos/README.md)

## Docker

A container image is published on Docker Hub as [hazemataya/hape](https://hub.docker.com/r/hazemataya/hape).

## Author

- LinkedIn: https://www.linkedin.com/in/hazem-ataya-29849b151/
- GitHub: https://github.com/hazemataya94
