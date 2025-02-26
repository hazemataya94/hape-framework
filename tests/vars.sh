export WORK_DIR="/workspace/playground"
export PROJECT_NAME="hello-world"
export PROJECT_NAME_SNAKE_CASE=$(echo "$PROJECT_NAME" | sed 's/-/_/g')
export TEST_MODEL="test-model"
export TEST_MODEL_SNAKE_CASE=$(echo "$TEST_MODEL" | sed 's/-/_/g')
export TEST_DELETE_MODEL="test-delete-model"
export TEST_DELETE_MODEL_SNAKE_CASE=$(echo "$TEST_DELETE_MODEL" | sed 's/-/_/g')
export COMMAND="hape"