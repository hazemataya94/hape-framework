#!/bin/bash
set -e
dir_name=$(dirname $0)
source "$dir_name/vars.sh"
cd ${WORK_DIR}

echo "Generating CRUD for project ${PROJECT_NAME}"
cd "${PROJECT_NAME}"

VAR='{
    "name": "deployment-cost-new",
    "schema": {
        "id": {"int": ["autoincrement"]},
        "service-name": {"string": []},
        "pod-cpu": {"string": []},
        "pod-ram": {"string": []},
        "autoscaling": {"bool": []},
        "min-replicas": {"int": ["nullable"]},
        "max-replicas": {"int": ["nullable"]},
        "current-replicas": {"int": []},
        "pod-cost": {"string": []},
        "number-of-pods": {"int": []},
        "total-cost": {"float": []},
        "cost-unit": {"string": []}
    }
}'

echo "$$ hape crud generate --json '$VAR'"
hape crud generate --json "$VAR"