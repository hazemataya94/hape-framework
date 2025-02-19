#!/bin/bash
set -e

[ -z "${WORK_DIR}" ] && source "$(dirname $0)/vars.sh"
cd ${WORK_DIR}
cd ${PROJECT_NAME}

echo "Deleting ${TEST_MODEL} CRUD"
echo "\$ ${COMMAND} crud delete --delete ${TEST_MODEL}"
${COMMAND} crud delete --name ${TEST_MODEL}

if [ -f "${PROJECT_NAME_SNAKE_CASE}/argument_parsers/${TEST_MODEL_SNAKE_CASE}_argument_parser.py" ]; then
    echo "Error: ${PROJECT_NAME_SNAKE_CASE}/argument_parsers/${TEST_MODEL_SNAKE_CASE}_argument_parser.py exists"
    exit 1
fi

if [ -f "${PROJECT_NAME_SNAKE_CASE}/controllers/${TEST_MODEL_SNAKE_CASE}_controller.py" ]; then
    echo "Error: ${PROJECT_NAME_SNAKE_CASE}/controllers/${TEST_MODEL_SNAKE_CASE}_controller.py exists"
    exit 1
fi

if [ -f "${PROJECT_NAME_SNAKE_CASE}/models/${TEST_MODEL_SNAKE_CASE}_model.py" ]; then
    echo "Error: ${PROJECT_NAME_SNAKE_CASE}/models/${TEST_MODEL_SNAKE_CASE}_model.py exists"
    exit 1
fi
