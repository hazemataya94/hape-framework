#!/bin/bash
set -e

[ -z "${WORK_DIR}" ] && source "$(dirname $0)/vars.sh"
cd ${WORK_DIR}
cd ${PROJECT_NAME}

echo "Copying .env file"
cp ../../.env ./

echo "Saving new models"

echo """
$ python main.py test-model save \
--service-name "test1" \
--pod-cpu 0.5 \
--pod-ram 1g \
--autoscaling false \
--current-replicas 2
"""
python main.py test-model save \
--service-name "test1" \
--pod-cpu 0.5 \
--pod-ram 1g \
--autoscaling false \
--current-replicas 2
echo "---"

echo """
$ python main.py test-model save \
--service-name "test2" \
--pod-cpu 0.5 \
--pod-ram 1g \
--autoscaling false \
--current-replicas 2
"""
python main.py test-model save \
--service-name "test2" \
--pod-cpu 0.5 \
--pod-ram 1g \
--autoscaling false \
--current-replicas 2
echo "---"

echo """
$ python main.py test-model save
    --service-name "test3"
    --pod-cpu 1
    --pod-ram 4g
    --autoscaling false
    --current-replicas 2
"""
python main.py test-model save \
--service-name "test3" \
--pod-cpu 1 \
--pod-ram 4g \
--autoscaling false \
--current-replicas 2
echo "---"

echo "Getting object by id"
echo "$ python main.py test-model get --id 1"
python main.py test-model get --id 1
echo "---"

echo "Getting object by service name"
echo "$ python main.py test-model get --service-name \"test3\""
python main.py test-model get --service-name "test3"
echo "---"

echo "Getting all objects"
echo "$ python main.py test-model get-all"
python main.py test-model get-all
echo "---"

echo "Getting all objects where pod-cpu is 0.5"
echo "$ python main.py test-model get-all --pod-cpu 0.5"
python main.py test-model get-all --pod-cpu 0.5
echo "---"

echo "Deleting object by id"
echo "$ python main.py test-model delete --id 1"
python main.py test-model delete --id 1
echo "---"

echo "Getting all objects"
echo "$ python main.py test-model get-all"
python main.py test-model get-all
echo "---"

echo "Deleting all objects"
echo "$ python main.py test-model delete-all"
python main.py test-model delete-all
echo "---"

echo "Getting all objects"
echo "$ python main.py test-model get-all"
python main.py test-model get-all

