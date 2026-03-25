<img src="https://raw.githubusercontent.com/hazemataya94/hape-framework/refs/heads/main/docs/logo.png" width="100%">

# HAPE Framework

The LLM agents have changed our world, software development world. Now to implement your vision, you just need a well guided LLM, and you'll implement your solution in no time.

This also applies to infrastructure, since nowadays everything is switching to IaC, and as long as you understand software architecture, working on infrastructure is not that different.

I'm starting this project on 22.02.2026 as a learning and research project to answer the question:
Is it still a dream to have a self healing infrastructure further pushing our advancement pace in technology.

The project is a newer version of HAPE Framework.<br>
https://github.com/hazemataya94/hape-framework-deprecated

## Table of Contents
- [Vision](#vision)
- [Intellectual Property / Permissions](#intellectual-property--permissions)
- [Contributions](#contributions)
- [Demos](#demos)
- [Architecture](#architecture)
- [Makefile](#makefile)
- [Documentation](#documentation)
- [Getting started](#getting-started)
- [Author](#author)

## Vision
Modern organizations manage hundreds of microservices, each with its own infrastructure, CI/CD, monitoring, and deployment configurations. This complexity increases the cognitive load on developers and slows down development operations.

HAPE Framework aims to reduce this complexity by enabling platform engineers to build automation tools to simplify the work, and to manage operational resources like AWS, Kubernetes, GitHub, GitLab, ArgoCD, Prometheus, Grafana, HashiCorp Vault, and many others, in a centralized and unified manner. These automation tools are reffered to as Internal Developer Platforms (IDPs).

HAPE Framework includes:
- Automation Platform based on Python CLI to automate daily work of Platform Engineers.
- Observation Platform based on Time Series Database to collect and analyze infrastructure status quo.
- Platform Agent based on LLM or Rule Engine AI (To Be Decided) to orchestrate automated decisions based on observation data.

## Intellectual Property / Permissions
Copyright (c) 2026 Hazem Ataya. All rights reserved.

This repository is **not licensed**. No permission is granted to use, copy, modify, merge, publish, distribute, sublicense, or sell any part of this repository or its contents without **explicit written permission** from the copyright holder.

## Contributions
Contributions are not accepted at the moment.

## Demos
- [Demos Directory](demos/README.md)

## Architecture
- [Architecture Document](docs/architecture.md)

## Makefile
- [Makefile Documentation](docs/makefile.md) - reference for Makefile variables, targets, and common workflows.

To list all available Make commands and their descriptions:

```bash
make help
```

## Documentation
- [Documentation Directory](docs/README.md)


## Getting started

Install HAPE with pip:

```bash
python3 -m pip install hape
```

Show available commands:

```bash
hape --help
```

Expected output:

```text
usage: hape [-h] [command] ...

CLI for platform and DevOps automations.

commands:
    config                      config file operations.
    gitlab                      GitLab operations.
    jira                        fetch Jira issue data, remote links, or add comments.
    confluence                  confluence page operations.
    csv                         csv conversion operations.
    dora                        DORA metrics operations.
    eks-deployment-cost         generate EKS Deployment/StatefulSet cost report.
    kube-agent                  investigate Kubernetes incidents from CLI triggers.
    init-cicd                   scaffold deployment and CI files for supported projects.
    markdown                    markdown table import/export operations.

options:
  -h, --help                    show this help message and exit
  --version                     print the installed hape version and exit.
  --config-file-path CONFIG_FILE_PATH
                                path to config.json (default: ~/.hape/config.json).
```

## Author
- LinkedIn: https://www.linkedin.com/in/hazem-ataya-29849b151/
- GitHub: https://github.com/hazemataya94
