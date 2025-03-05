#!/bin/bash
set -e

[ -z "${WORK_DIR}" ] && source "$(dirname $0)/vars.sh"
cd ${WORK_DIR}
cd ${PROJECT_NAME}

MODEL_JSON_SCHEMA='{
    "test-delete-model": {
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

echo "\$ ${COMMAND} crud generate --json '$MODEL_JSON_SCHEMA'"
${COMMAND} crud generate --json "$MODEL_JSON_SCHEMA"

if [ ! -f "${PROJECT_NAME_SNAKE_CASE}/argument_parsers/${TEST_DELETE_MODEL_SNAKE_CASE}_argument_parser.py" ]; then
    echo "Error: ${PROJECT_NAME_SNAKE_CASE}/argument_parsers/${TEST_DELETE_MODEL_SNAKE_CASE}_argument_parser.py does not exist"
    exit 1
fi

if [ ! -f "${PROJECT_NAME_SNAKE_CASE}/controllers/${TEST_DELETE_MODEL_SNAKE_CASE}_controller.py" ]; then
    echo "Error: ${PROJECT_NAME_SNAKE_CASE}/controllers/${TEST_DELETE_MODEL_SNAKE_CASE}_controller.py does not exist"
    exit 1
fi

if [ ! -f "${PROJECT_NAME_SNAKE_CASE}/models/${TEST_DELETE_MODEL_SNAKE_CASE}_model.py" ]; then
    echo "Error: ${PROJECT_NAME_SNAKE_CASE}/models/${TEST_DELETE_MODEL_SNAKE_CASE}_model.py does not exist"
    exit 1
fi


echo "Deleting ${TEST_DELETE_MODEL} CRUD"
echo "\$ ${COMMAND} crud delete --delete ${TEST_DELETE_MODEL}"
${COMMAND} crud delete --name ${TEST_DELETE_MODEL}

echo "Checking if ${TEST_DELETE_MODEL} CRUD is deleted properly"
if [ -f "${PROJECT_NAME_SNAKE_CASE}/argument_parsers/${TEST_DELETE_MODEL_SNAKE_CASE}_argument_parser.py" ]; then
    echo "Error: ${PROJECT_NAME_SNAKE_CASE}/argument_parsers/${TEST_DELETE_MODEL_SNAKE_CASE}_argument_parser.py exists"
    exit 1
fi

if [ -f "${PROJECT_NAME_SNAKE_CASE}/controllers/${TEST_DELETE_MODEL_SNAKE_CASE}_controller.py" ]; then
    echo "Error: ${PROJECT_NAME_SNAKE_CASE}/controllers/${TEST_DELETE_MODEL_SNAKE_CASE}_controller.py exists"
    exit 1
fi

if [ -f "${PROJECT_NAME_SNAKE_CASE}/models/${TEST_DELETE_MODEL_SNAKE_CASE}_model.py" ]; then
    echo "Error: ${PROJECT_NAME_SNAKE_CASE}/models/${TEST_DELETE_MODEL_SNAKE_CASE}_model.py exists"
    exit 1
fi

TEST_MODEL_NAME="TestDeleteModel"
MAIN_ARGUMENT_PARSER_MODEL_LINES=$(cat ${PROJECT_NAME_SNAKE_CASE}/argument_parsers/main_argument_parser.py | grep ${TEST_MODEL_NAME}ArgumentParser || echo "")
lines_count=$(echo "$MAIN_ARGUMENT_PARSER_MODEL_LINES" | grep -c "" || echo "0")

if [ -n "$MAIN_ARGUMENT_PARSER_MODEL_LINES" ] || [ "$lines_count" -gt 1 ]; then
    echo "Error: ${TEST_MODEL_NAME}ArgumentParser is not deleted properly in main_argument_parser.py"
    exit 1
fi
