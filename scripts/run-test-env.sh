#!/bin/bash

docker build -t test -f .dockerfiles/Dockerfile.dev .

docker run --rm -it \
    -e GITLAB_TOKEN=${GITLAB_TOKEN} \
    -e GITLAB_DOMAIN=${GITLAB_DOMAIN} \
    -e AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id) \
    -e AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key) \
    -e AWS_DEFAULT_REGION=eu-central-1 \
    -e AWS_PAGER="" \
    -v ~/.ssh:/root/.ssh \
    test bash
    # -v .:/workspace \