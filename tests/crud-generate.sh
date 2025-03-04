#!/bin/bash
set -e

[ -z "${WORK_DIR}" ] && source "$(dirname $0)/vars.sh"
cd ${WORK_DIR}
cd ${PROJECT_NAME}

echo "Generating ${TEST_MODEL} CRUD"
MODEL_JSON_SCHEMA='{
    "test-model": {
        "id": {"int": ["primary", "autoincrement"]},
        "service-name": {"string": []},
        "pod-cpu": {"string": []},
        "pod-ram": {"string": []},
        "autoscaling": {"bool": []},
        "min-replicas": {"int": ["nullable"]},
        "max-replicas": {"int": ["nullable"]},
        "current-replicas": {"int": []}
    },
    "test-model-cost": {
        "id": {"int": ["primary", "autoincrement"]},
        "test-model-id": {"int": ["required", "foreign-key(test-model.id, on-delete=cascade)"]},
        "pod-cost": {"string": []},
        "number-of-pods": {"int": []},
        "total-cost": {"float": []}
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

TEST_MODEL_NAME="TestModel"
MAIN_ARGUMENT_PARSER_MODEL_LINES=$(cat ${PROJECT_NAME_SNAKE_CASE}/argument_parsers/main_argument_parser.py | grep ${TEST_MODEL_NAME}ArgumentParser) || echo ""

line_count=$(echo "$MAIN_ARGUMENT_PARSER_MODEL_LINES" | grep -c ${TEST_MODEL_NAME}ArgumentParser) || echo "0"
if [ "$line_count" != 3 ]; then
    echo "Error: ${TEST_MODEL_NAME}ArgumentParser is not added properly in main_argument_parser.py"
    exit 1
fi

line_count=$(echo "$MAIN_ARGUMENT_PARSER_MODEL_LINES" | grep -c "import ${TEST_MODEL_NAME}ArgumentParser") || echo "0"
if [ "$line_count" != 1 ]; then
    echo "Error: import ${TEST_MODEL_NAME}ArgumentParser is not added properly in main_argument_parser.py"
    exit 1
fi

line_count=$(echo "$MAIN_ARGUMENT_PARSER_MODEL_LINES" | grep -c "${TEST_MODEL_NAME}ArgumentParser().create_subparser") || echo "0"
if [ "$line_count" != 1 ]; then
    echo "Error: ${TEST_MODEL_NAME}ArgumentParser.create_subparser is not added properly in main_argument_parser.py"
    exit 1
fi

line_count=$(echo "$MAIN_ARGUMENT_PARSER_MODEL_LINES" | grep -c "${TEST_MODEL_NAME}ArgumentParser().run_action(args)") || echo "0"
if [ "$line_count" != 1 ]; then
    echo "Error: ${TEST_MODEL_NAME}ArgumentParser.run_action is not added properly in main_argument_parser.py"
    exit 1
fi
