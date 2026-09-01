# Installation

## Purpose

Install the published `hape` CLI on a local workstation.

## Prerequisites

- Python 3.9 or later.
- `pip` available as `python -m pip`.

## Install from PyPI

```bash
python -m pip install hape
hape --version
hape --help
```

Expected: the installed version prints, then the command groups print.

## Install from a clone

Use this path when you are contributing to the repository.

```bash
python -m pip install -r requirements-build.txt
make build
make install
hape --version
```

Expected: the local wheel installs into `.exec-venv` and `hape --version` prints the repository `VERSION`.

See [build and install](../dev/build-and-install.md) for maintainer details.

## Docker

```bash
docker pull hazemataya/hape:latest
docker run --rm hazemataya/hape:latest
```

Expected: container help output for the `hape` CLI.

## Related documentation

- [Five-minute quick start](five-minute-quickstart.md)
- [Configuration](configuration.md)
- [CLI usage](../cli/cli.md)
