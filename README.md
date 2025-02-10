# HAPE Framework: Overview & Features

## What is HAPE Framework?
HAPE Framework is a lightweight and extensible Python framework designed to help platform engineers build customized CLI and API-driven platforms with minimal effort. It provides a structured way to develop orchestrators for managing infrastructure, CI/CD pipelines, cloud resources, and other platform engineering needs. 

HAPE is built around abstraction and automation, allowing engineers to define and manage resources like AWS, Kubernetes, GitHub, GitLab, ArgoCD, Prometheus, Grafana, HashiCorp Vault, and many others in a unified manner. It eliminates the need to manually integrate multiple packages for each tool, offering a streamlined way to build self-service developer portals and engineering platforms. 

## Idea Origin
Modern organizations manage hundreds of microservices, each with its own infrastructure, CI/CD, monitoring, and deployment configurations. This complexity increases the cognitive load on developers and slows down platform operations. 

HAPE Framework aims to reduce this complexity by enabling platform engineers to build opinionated, yet flexible automation tools that simplify the work to build a platform. 

With HAPE, developers can interact with a CLI or API to create, deploy, and manage their services without diving into complex configurations. The framework also supports custom state management via databases, and integration with existing DevOps tools. 

## Done Features
### Automate everyday commands
```
$ make list
build                Build the package in dist. Runs: bump-version.
bump-version         Bump the patch version in setup.py.
clean                Clean up build, cache, playground and zip files.
docker-down          Stop Docker services.
docker-exec          Execute a shell in the HAPE Docker container.
docker-ps            List running Docker services.
docker-restart       Restart Docker services.
docker-up            Start Docker services.
freeze-cli           Freeze dependencies for CLI.
freeze-dev           Freeze dependencies for development.
init-cli             Install CLI dependencies.
init-dev             Install development dependencies in .venv, start docker services, and create .env if not exist.
install              Install the package.
list                 List available commands and description.
migration-create     Create a new database migration.
migration-run        Apply the latest database migrations.
play                 Run hape.playground Playground.paly() and print execution time.
publish              Publish package to public PyPI, commit, tag, and push version. Runs: build.
publish-aws          Publish package to AWS CodeArtifact. Runs: build.
source-env           Print export statements for all environment variables from .env file.
zip                  Create a zip archive excluding local git, env, venv and playground.
```

### Publish to public PyPI repository
```
$ pip install --upgrade hape
$ hape --version
0.x.x
```

## In Progress Features

### Support Initializing Project
```
$ hape init --help
usage: hape init [-h] {project} ...

positional arguments:
  {project}
    project   Initializes a new project

options:
  -h, --help  show this help message and exit
$ hape init project --name myawesomeplatform
myawesomeplatform/
│── dockerfiles/  (Copied from HAPE Framework)
│── Makefile      (Copied from HAPE Framework)
│── src/
│   ├── migrations/
│   ├── models/
│   ├── controllers/
│   ├── services/
│   ├── utils/
│   ├── config/
│   ├── tests/
│── docs/
│── scripts/
│── setup.py
│── README.md
```

## TODO Features
### Support CRUD Generate and Create migrations/json/model_name.json 
```
$ hape crud generate --json """
{
    "name": "deployment-cost"
    "schema": {
        "id": ["int","autoincrement"],
        "service-name": ["string"],
        "pod-cpu": ["string"],
        "pod-ram": ["string"],
        "autoscaling": ["bool"],
        "min-replicas": ["int","nullable"],
        "max-replicas": ["int","nullable"],
        "current-replicas": ["int"],
        "pod-cost": ["string"],
        "number-of-pods": ["int"],
        "total-cost": ["float"],
        "cost-unit": ["string"]
    }
}
"""
$ hape deployment-cost --help
usage: myawesomeplatform deployment-cost [-h] {save,get,get-all,delete,delete-all} ...

positional arguments:
  {save,get,get-all,delete,delete-all}
    save                Save DeploymentCost object based on passed arguments or filters
    get                 Get DeploymentCost object based on passed arguments or filters
    get-all             Get-all DeploymentCost objects based on passed arguments or filters
    delete              Delete DeploymentCost object based on passed arguments or filters
    delete-all          Delete-all DeploymentCost objects based on passed arguments or filters

options:
  -h, --help            show this help message and exit
```

### Create migrations/json/model_name.json and run CRUD Geneartion for file in migrations/schema_json/{*}.json if models/file.py doesn't exist
```
$ export MY_JSON_FILE="""
{
    "name": "deployment-cost"
    "schema": {
        "id": ["int","autoincrement"],
        "service-name": ["string"],
        "pod-cpu": ["string"],
        "pod-ram": ["string"],
        "autoscaling": ["bool"],
        "min-replicas": ["int","nullable"],
        "max-replicas": ["int","nullable"],
        "current-replicas": ["int"],
        "pod-cost": ["string"],
        "number-of-pods": ["int"],
        "total-cost": ["float"],
        "cost-unit": ["string"]
    }
}
"""
$ echo "${MY_JSON_FILE}" > migrations/schema_json/deployment_cost.json
$ hape crud generate
$ hape deployment-cost --help
usage: hape deployment-cost [-h] {save,get,get-all,delete,delete-all} ...

positional arguments:
  {save,get,get-all,delete,delete-all}
    save                Save DeploymentCost object based on passed arguments or filters
    get                 Get DeploymentCost object based on passed arguments or filters
    get-all             Get-all DeploymentCost objects based on passed arguments or filters
    delete              Delete DeploymentCost object based on passed arguments or filters
    delete-all          Delete-all DeploymentCost objects based on passed arguments or filters

options:
  -h, --help            show this help message and exit
```

### Support Scalable Secure RESTful API
```
$ hape serve http --allow-cidr '0.0.0.0/0,10.0.1.0/24' --deny-cidr '10.200.0.0/24,0,10.0.1.0/24,10.107.0.0/24' --workers 2 --port 80
or
$ hape serve http --json """
{
    "port": 8088
    "allow-cidr": "0.0.0.0/0,10.0.1.0/24",
    "deny-cidr": "10.200.0.0/24,0,10.0.1.0/24,10.107.0.0/24"
}
"""
Spawnining workers
hape-worker-random-string-1 is up
hape-worker-random-string-2 failed
hape-worker-random-string-2 restarting (up to 3 times)
hape-worker-random-string-2 is up
All workers are up
Database connection established
Any other needed step

Serving HAPE on http://127.0.0.1:8088
```
