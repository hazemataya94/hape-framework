#!/bin/bash
set -e
dir_name=$(dirname $0)
source "$dir_name/vars.sh"
cd ${WORK_DIR}

echo "Initializing project ${PROJECT_NAME}"

apt update && apt install -y tree

hape init project --name ${PROJECT_NAME}

tree ${PROJECT_NAME} -L 3
