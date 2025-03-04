#!/usr/bin/env bats

setup() {
  export WORK_DIR="/tmp/hape_tests"
  export PROJECT_NAME="test_project"
  mkdir -p "$WORK_DIR"
  cd "$WORK_DIR"
}

@test "Install Hape CLI" {
  run pip install --upgrade hape
  [ "$status" -eq 0 ] || fail "Hape installation failed"
  run hape --version
  [[ "$output" == *"hape v"* ]] || fail "Hape version check failed"
}

@test "Initialize project structure" {
  run hape init project --name "$PROJECT_NAME"
  [ "$status" -eq 0 ] || fail "Project initialization failed"
  [[ -d "$PROJECT_NAME" ]] || fail "Project directory not found"
}

@test "CRUD generate creates new model files" {
  cd "$WORK_DIR/$PROJECT_NAME"
  MODEL_JSON='{"name": "test_model", "fields": [{"name": "title", "type": "string"}]}'
  run hape crud generate --json "$MODEL_JSON"
  [ "$status" -eq 0 ] || fail "CRUD generation failed"
  [[ -f "test_project/argument_parsers/test_model_argument_parser.py" ]] || fail "Argument parser file not found"
}

@test "CRUD delete removes model files" {
  cd "$WORK_DIR/$PROJECT_NAME"
  run hape crud delete --name "test_model"
  [ "$status" -eq 0 ] || fail "CRUD deletion failed"
  [[ ! -f "test_project/argument_parsers/test_model_argument_parser.py" ]] || fail "Argument parser file still exists"
}
