dir_name=$(dirname $0)
source "$dir_name/vars.sh"
cd ${WORK_DIR}

cd "${PROJECT_NAME}"

echo "$$ hape crud delete --delete deployment-cost-new"
hape crud delete --name deployment-cost-new

