# HAPE Framework: Overview & Features

## Overview

Modern organizations manage hundreds of microservices, each with its own infrastructure, CI/CD, monitoring, and deployment configurations. This complexity increases the cognitive load on developers and slows down development operations. 

HAPE Framework aims to reduce this complexity by enabling platform engineers to build automation tools to simplify the work, and to manage operational resources like AWS, Kubernetes, GitHub, GitLab, ArgoCD, Prometheus, Grafana, HashiCorp Vault, and many others, in a centralized and unified manner. These automation tools are reffered to as Internal Developer Platforms (IDPs).

HAPE Framework is a CLI and API driven Python framework targeted for Platform Engineers to build Internal Developer Platforms (IDPs).

## Done Features
### Automate everyday commands
```sh
$ make list
build                Build the package in dist. Runs: bump-version.
bump-version         Bump the patch version in setup.py.
clean                Clean up build, cache, playground and zip files.
docker-build-prod    Build the production Docker image.
docker-down          Stop Docker services.
docker-exec          Execute a shell in the HAPE Docker container.
docker-ps            List running Docker services.
docker-python        Runs a Python container in playground directory.
docker-restart       Restart Docker services.
docker-up            Start Docker services.
freeze-cli           Freeze dependencies for CLI.
freeze-dev           Freeze dependencies for development.
git-hooks            Install hooks in .git-hooks/ to .git/hooks/.
init-cli             Install CLI dependencies.
init-dev             Install development dependencies in .venv, docker-compose up -d, and create .env if not exist.
install              Install the package.
list                 Show available commands.
migration-create     Create a new database migration.
migration-run        Apply the latest database migrations.
play                 Run hape.playground Playground.paly() and print the execution time.
publish              Runs test-code, build, and publish package to public PyPI. Commit, tag, and push the version. Runs test-cli to test the published package and make sure it works.
reset-data           Deletes hello-world project from previous tests, drops and creates database hape_db.
reset-local          Deletes hello-world project from previous tests, drops and creates database hape_db, runs migrations, and runs the playground.
source-env           Print export statements for the environment variables from .env file.
test-cli             Run a new python container, installs hape cli and runs all tests inside it.
test-code            Runs containers in dockerfiles/docker-compose.yml, Deletes hello-world project from previous tests, and run all code automated tests.
zip                  Create a zip archive excluding local files and playground.
```

### Publish to public PyPI repository
```sh
$ make publish
Making sure hape container is running
hape             hape:dev                "sleep infinity"         hape         9 hours ago   Up 9 hours   
Removing hello-world project from previous tests
Dropping and creating database hape_db
...
Running all code tests
=============================================================
Running ./tests/init-project.sh
--------------------------------
Installing tree if not installed
Deleting project hello-world if exists
...
🔄 Bumping patch version in setup.py...
Version updated to 0.x.x
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - setuptools >= 40.8.0
...
Successfully built hape-0.x.x.tar.gz and hape-0.x.x-py3-none-any.whl
Uploading distributions to https://upload.pypi.org/legacy/
Uploading hape-0.x.x-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 63.6/63.6 kB • 00:00 • 55.1 MB/s
Uploading hape-0.x.x.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 54.3/54.3 kB • 00:00 • 35.6 MB/s
...
View at:
https://pypi.org/project/hape/0.x.x/
...
Pushing commits
Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
...
Pushing tags
Total 0 (delta 0), reused 0 (delta 0), pack-reused 0
To github.com:hazemataya94/hape-framework.git
 * [new tag]         0.x.x -> 0.x.x
...
Python files changes detected, running code tests...
Removing hello-world project from previous tests
Dropping and creating database hape_db
Running all tests in hape container defined in dockerfiles/docker-compose.yml
=============================================================
Running all code tests
...
Deleted: hello_world/controllers/test_delete_model_controller.py
Deleted: hello_world/argument_parsers/test_delete_model_argument_parser.py
All model files -except the migration file- have been deleted successfully!
---
Migration file location: hello_world/migrations/versions
Make sure to modify the migration file to stop the model table creation, or delete the migration file manually if you don't want it anymore.
=============================================================
        6.62 real         0.01 user         0.02 sys
All tests finished successfully!
```

### Install latest `hape` CLI
```sh
$ make install
```
or
```sh
$ pip install --upgrade hape
```

### Support Initializing Project
```sh
$ hape init project --name hello-world
Project hello-world has been successfully initialized!
$ tree hello-world 
hello-world
├── MANIFEST.in
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
│   │   ├── json
│   │   │   └── 000001_migration.json
│   │   ├── script.py.mako
│   │   ├── versions
│   │   │   └── 000001_migration.py
│   │   └── yaml
│   │       └── 000001_migration.yaml
│   ├── models
│   │   ├── __init__.py
│   │   └── test_model_cost_model.py
│   ├── playground.py
│   └── services
│       └── __init__.py
├── main.py
├── requirements-cli.txt
├── requirements-dev.txt
└── setup.py
```

### Generate CRUD JSON Schema
```sh
$ hape json get --model-schema
{
    "valid_types": ["string", "text", "int", "bool", "float", "date", "datetime", "timestamp"],
    "valid_properties": ["nullable", "required", "unique", "primary", "autoincrement", "foreign-key", "index"],
    "valid_foreign_key_on_delete": ["cascade", "set-null", "set-default", "restrict", "no-action"],
    "foreign_key_syntax": "foreign-key(foreign-key-model.foreign-key-attribute, on-delete=foreign-key-on-delete)",
    
    "model-name": {
        "column_name": {"valid-type": ["valid-property"]},
        "id": {"valid-type": ["valid-property"]},
        "updated_at": {"valid-type": []},
        "name": {"valid-type": ["valid-property", "valid-property"]},
        "enabled": {"valid-type": []},
    }
    
    "example-model": {
        "id": {"int": ["primary"]},
        "updated_at": {"timestamp": []},
        "name": {"string": ["required", "unique"]},
        "enabled": {"bool": []}
    }
}
```

### Generate CRUD YAML Schema
```sh
$ hape yaml get --model-schema
valid_types: ["string", "text", "int", "bool", "float", "date", "datetime", "timestamp"]
valid_properties: ["nullable", "required", "unique", "primary", "autoincrement", "foreign-key", "index"]
valid_foreign_key_on_delete: ["cascade", "set-null", "set-default", "restrict", "no-action"]
foreign_key_syntax: "foreign-key(foreign-key-model.foreign-key-attribute, on-delete=foreign-key-on-delete)"

model-name:
  column_name:
    valid-type: 
      - valid-property
  id:
    valid-type: 
      - valid-property
  updated_at:
    valid-type: []
  name:
    valid-type: 
      - valid-property
      - valid-property
  enabled:
    valid-type: []

example-model:
  id:
    int: 
      - primary
  updated_at:
    timestamp: []
  name:
    string: 
      - required
      - unique
  enabled:
    bool: []
```

### Support CRUD Generate and Create migrations/json/model_name.json and migrations/yaml/model_name.yaml
```sh
$ hape crud generate --json '
{
    "k8s-deployment": {
        "id": {"int": ["primary", "autoincrement"]},
        "service-name": {"string": []},
        "pod-cpu": {"string": []},
        "pod-ram": {"string": []},
        "autoscaling": {"bool": []},
        "min-replicas": {"int": ["nullable"]},
        "max-replicas": {"int": ["nullable"]},
        "current-replicas": {"int": []}
    },
    "test-deployment-cost": {
        "id": {"int": ["primary", "autoincrement"]},
        "test-deployment-id": {"int": ["required", "foreign-key(test-deployment.id, on-delete=cascade)"]},
        "pod-cost": {"string": []},
        "number-of-pods": {"int": []},
        "total-cost": {"float": []}
    }
}'
Generated: hello_world/argument_parsers/k8s_deployment_argument_parser.py
Generated: hello_world/controllers/k8s_deployment_controller.py
Generated: hello_world/models/k8s_deployment_model.py
Generated: hello_world/argument_parsers/test_deployment_cost_argument_parser.py
Generated: hello_world/controllers/test_deployment_cost_controller.py
Generated: hello_world/models/test_deployment_cost_model.py
Generated: hello_world/migrations/versions/000001_migration.py
Generated: hello_world/migrations/json/000001_migration.json
Generated: hello_world/migrations/yaml/000001_migration.yaml
```

## In Progress Features
### Create GitHub Project to Manage issues, tasks and future workfr

### Support CRUD CLI for CRUD generated models
```sh
$ hape k8s-deployment-cost --help
usage: hello-world k8s-deployment-cost [-h] {save,get,get-all,delete,delete-all} ...

positional arguments:
  {save,get,get-all,delete,delete-all}
    save                Save K8SDeploymentCost object based on passed arguments or filters
    get                 Get K8SDeploymentCost object based on passed arguments or filters
    get-all             Get-all K8SDeploymentCost objects based on passed arguments or filters
    delete              Delete K8SDeploymentCost object based on passed arguments or filters
    delete-all          Delete-all K8SDeploymentCost objects based on passed arguments or filters

options:
  -h, --help            show this help message and exit
```

## TODO for 0.3.1:
### Use draft.json and draft.yaml to generate CRUD files
The model schema is defined in migrations/json/draft.json, or migrations/yaml/draft.yaml, based on the passed flag.
```sh
$ hape crud generate --json/-j
$ hape crud generate --yaml/-y
```

### Pass file.json or file.yaml which contains the model json or yaml schema to generate CRUD files
```sh
$ hape crud generate -j -f path/to/file.json
$ hape crud generate -y -f path/to/file.yaml
```

### Publish docker image to public repository
```sh
$ make docker-build-prod
$ make docker-push
```

### Create a Publish Workflow using Makefile Actions
Add publish-pre-actions, publish-post-actions, publish-cli actions to Makefile and modify publish workflow.
```sh
$ make publish
Running:
- publish-pre-actions
- publish-cli
- publish-docker
- publish-post-actions
```

### Generate CHANGELOG.md
```sh
$ hape changelog generate # generate CHANGELOG.md from scratch
$ hape changelog update # append missing versions to CHANGELOG.md
```

### Create code documentation as markdown files in docs/developer and docs/user directories
```sh
$ hape docs generate
```

## Backlog:
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

## Project
Feel free to explore the [HAPE Framework Github Project](https://github.com/users/hazemataya94/projects/1).
