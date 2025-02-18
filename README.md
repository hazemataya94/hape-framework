![HAPE Framework](docs/logo.png)

# HAPE Framework: Overview & Features

## What is HAPE Framework?
HAPE Framework is a lightweight and extensible Python framework designed to help platform engineers build customized CLI and API-driven platforms with minimal effort. It provides a structured way to develop orchestrators for managing infrastructure, CI/CD pipelines, cloud resources, and other platform engineering needs. 

HAPE Framework is built around abstraction and automation, allowing engineers to define and manage resources like AWS, Kubernetes, GitHub, GitLab, ArgoCD, Prometheus, Grafana, HashiCorp Vault, and many others in a unified manner. It eliminates the need to manually integrate multiple packages for each tool, offering a streamlined way to build self-service developer portals and engineering platforms. 

## Idea Origin
Modern organizations manage hundreds of microservices, each with its own infrastructure, CI/CD, monitoring, and deployment configurations. This complexity increases the cognitive load on developers and slows down platform operations. 

HAPE Framework aims to reduce this complexity by enabling platform engineers to build opinionated, yet flexible automation tools that simplify the work to build a platform. 

With HAPE, developers can interact with a CLI or API to create, deploy, and manage their services without diving into complex configurations. The framework also supports custom state management via databases, and integration with existing DevOps tools. 

## Done Features
### Automate everyday commands
```sh
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
```sh
$ make publish
🔄 Bumping patch version in setup.py...
Version updated to 0.x.x
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - setuptools >= 40.8.0
* Getting build dependencies for sdist...
0.x.x
.
Successfully built hape-0.x.x.tar.gz and hape-0.x.x-py3-none-any.whl
Uploading distributions to https://upload.pypi.org/legacy/
Uploading hape-0.x.x-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 63.6/63.6 kB • 00:00 • 55.1 MB/s
Uploading hape-0.x.x.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 54.3/54.3 kB • 00:00 • 35.6 MB/s
.
View at:
https://pypi.org/project/hape/0.x.x/
.
Pushing commits
Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
.
Pushing tags
Total 0 (delta 0), reused 0 (delta 0), pack-reused 0
To github.com:hazemataya94/hape-framework.git
 * [new tag]         0.x.x -> 0.x.x
$ pip install --upgrade hape
$ hape --version
0.x.x
```

### Support Initializing Project
```sh
$ hape init project --help
usage: hape init project [-h] -n NAME

options:
  -h, --help       show this help message and exit
  -n, --name NAME  Name of the project
$ pip install --upgrade hape > /dev/null 2>&1
$ hape init project --name hello-world
Project hello-world has been successfully initialized!
$ tree hello-world 
hello-world
├── Makefile
├── README.md
├── alembic.ini
├── dockerfiles
│   ├── Dockerfile.dev
│   ├── Dockerfile.prod
│   └── docker-compose.yml
├── hello_world
│   ├── __init__.py
│   ├── argument_parsers
│   │   ├── __init__.py
│   │   ├── main_argument_parser.py
│   │   └── playground_argument_parser.py
│   ├── bootstrap.py
│   ├── cli.py
│   ├── controllers
│   │   └── __init__.py
│   ├── enums
│   │   └── __init__.py
│   ├── migrations
│   │   ├── README
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions
│   ├── models
│   │   └── __init__.py
│   ├── playground.py
│   └── services
│       └── __init__.py
├── main.py
├── requirements-cli.txt
├── requirements-dev.txt
└── setup.py
```

## In Progress Features
### Support CRUD Generate and Create migrations/json/model_name.json 
```sh
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

## TODO Features

### Create migrations/json/model_name.json and run CRUD Geneartion for file in migrations/schema_json/{*}.json if models/file.py doesn't exist
```sh
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

### Generate CHANGELOG.md
```sh
$ hape changelog generate
$ echo "empty" > file.txt
$ git add file.txt
$ git commit -m "empty"
$ git push
$ make publish
$ hape changelog generate # generate CHANGELOG.md from scratch
$ hape changelog update # append missing versions to CHANGELOG.md
```

### Support Scalable Secure RESTful API
```sh
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
```sh
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

### Support CRUD Environment Variables
```sh
$ hape env add --key MY_ENV_KEY --value MY_ENV_VALUE
$ hape env get --key MY_ENV_KEY
MY_ENV_KEY=MY_ENV_VALUE
$ hape env delete --key MY_ENV_KEY
$ hape env get --key MY_ENV_KEY
MY_ENV_KEY=MY_ENV_VALUE
```

### Store Configuration in Database
```sh
$ hape config add --key MY_CONFIG_KEY --value MY_CONFIG_VALUE
$ hape config set --key MY_CONFIG_KEY --value MY_CONFIG_VALUE
$ hape config set --key MY_CONFIG_KEY --value MY_CONFIG_VALUE
$ hape config get --key MY_CONFIG_KEY
MY_CONFIG_KEY=MY_CONFIG_VALUE
$ hape config delete --key MY_CONFIG_KEY
$ hape config get --key MY_CONFIG_KEY
MY_CONFIG_KEY=MY_CONFIG_VALUE
```

### Run Using Environment Variables or Database Configuration
```sh
$ hape config set --config_source env
$ hape config set --config_source db
$ hape config set --config_env_prefix MY_ENV_PREFIX
```
