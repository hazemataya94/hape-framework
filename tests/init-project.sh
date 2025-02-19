#!/bin/bash
set -e

[ -z "${WORK_DIR}" ] && source "$(dirname $0)/vars.sh"
cd ${WORK_DIR}

echo "Installing tree if not installed"
if ! command -v tree &> /dev/null; then
    apt update && apt install -y tree
fi

echo "Deleting project ${PROJECT_NAME} if exists"
rm -rf ${PROJECT_NAME} || true

echo "Initializing project ${PROJECT_NAME}"
echo "\$ ${COMMAND} init project --name ${PROJECT_NAME}"
${COMMAND} init project --name ${PROJECT_NAME}
tree ${PROJECT_NAME} -L 3
