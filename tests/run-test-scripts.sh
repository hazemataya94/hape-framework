#!/bin/bash
set -e

dir_name=$(dirname $0)
source "${dir_name}/vars.sh"

if [ -z "$1" ]; then
    echo "Usage: $0 <code|cli>"
    exit 1
fi

if [ "$1" == "code" ]; then
    COMMAND="python /workspace/main_cli.py"
    test_scripts=(
        "init-project.sh"
        "crud-generate.sh"
        # "crud-delete.sh"
    )
elif [ "$1" == "cli" ]; then
    COMMAND="hape"
    test_scripts=(
        "install-hape.sh"
        "init-project.sh"
        "crud-generate.sh"
        # "crud-delete.sh"
    )
else
    echo "Usage: $0 <code|cli>"
    exit 1
fi

echo "============================================================="
echo "Running all ${1} tests"
echo "============================================================="

for script in "${test_scripts[@]}"; do
    echo "Running ${dir_name}/scripts/${script}"
    echo "--------------------------------"
    ${dir_name}/scripts/${script}
    echo "============================================================="
done
