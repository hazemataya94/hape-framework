#!/bin/bash
set -e

[ -z "${WORK_DIR}" ] && source "$(dirname $0)/vars.sh"
cd ${WORK_DIR}
cd ${PROJECT_NAME}

echo "Running CRUD functionality tests"
## save
## get
## get-all
## delete
## delete-all


echo "\$ ${COMMAND} crud functionality"
${COMMAND} crud functionality

