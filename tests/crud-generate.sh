#!/bin/bash
set -e

[ -z "${WORK_DIR}" ] && source "$(dirname $0)/vars.sh"
cd ${WORK_DIR}
cd ${PROJECT_NAME}

echo "Generating ${TEST_MODEL} CRUD"
MODEL_JSON_SCHEMA='{
    "{{model_name}}": {
        "id": {"int": ["primary", "autoincrement"]},
        "service-name": {"string": []},
        "pod-cpu": {"string": []},
        "pod-ram": {"string": []},
        "autoscaling": {"bool": []},
        "min-replicas": {"int": ["nullable"]},
        "max-replicas": {"int": ["nullable"]},
        "current-replicas": {"int": []}
    }
}'
MODEL_JSON_SCHEMA=$(echo "$MODEL_JSON_SCHEMA" | sed "s/{{model_name}}/${TEST_MODEL}/g")

echo "\$ ${COMMAND} crud generate --json '$MODEL_JSON_SCHEMA'"
${COMMAND} crud generate --json "$MODEL_JSON_SCHEMA"

if [ ! -f "${PROJECT_NAME_SNAKE_CASE}/argument_parsers/${TEST_MODEL_SNAKE_CASE}_argument_parser.py" ]; then
    echo "Error: ${PROJECT_NAME_SNAKE_CASE}/argument_parsers/${TEST_MODEL_SNAKE_CASE}_argument_parser.py does not exist"
    exit 1
fi

if [ ! -f "${PROJECT_NAME_SNAKE_CASE}/controllers/${TEST_MODEL_SNAKE_CASE}_controller.py" ]; then
    echo "Error: ${PROJECT_NAME_SNAKE_CASE}/controllers/${TEST_MODEL_SNAKE_CASE}_controller.py does not exist"
    exit 1
fi

if [ ! -f "${PROJECT_NAME_SNAKE_CASE}/models/${TEST_MODEL_SNAKE_CASE}_model.py" ]; then
    echo "Error: ${PROJECT_NAME_SNAKE_CASE}/models/${TEST_MODEL_SNAKE_CASE}_model.py does not exist"
    exit 1
fi
