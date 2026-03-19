variable "github_owner" {
  type = string
}

variable "github_token" {
  type      = string
  sensitive = true
}

variable "default_branch" {
  type    = string
  default = "main"
}

variable "repository_visibility" {
  type    = string
  default = "private"
}

variable "repository_names" {
  type = list(string)
  default = [
    "hape-dora-demo-service-a",
    "hape-dora-demo-service-b",
    "hape-dora-demo-service-c",
    "hape-dora-demo-service-d",
    "hape-dora-demo-service-e",
    "hape-dora-demo-service-f",
    "hape-dora-demo-service-g",
    "hape-dora-demo-service-h",
    "hape-dora-demo-service-i",
    "hape-dora-demo-service-j",
    "hape-dora-demo-service-k",
    "hape-dora-demo-service-l",
    "hape-dora-demo-service-m",
    "hape-dora-demo-service-n",
    "hape-dora-demo-service-o",
    "hape-dora-demo-service-p",
    "hape-dora-demo-service-q",
    "hape-dora-demo-service-r",
    "hape-dora-demo-service-s",
    "hape-dora-demo-service-t",
    "hape-dora-demo-service-u",
    "hape-dora-demo-service-v",
    "hape-dora-demo-service-w",
    "hape-dora-demo-service-x",
    "hape-dora-demo-service-y",
    "hape-dora-demo-service-z"
  ]
}

variable "sample_ci_content" {
  type    = string
  default = <<-EOT
name: deploy

on:
  workflow_dispatch:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy
        run: echo "deploy to kind"
EOT
}

variable "sample_manifest_content" {
  type    = string
  default = <<-EOT
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-app
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: sample-app
  template:
    metadata:
      labels:
        app: sample-app
    spec:
      containers:
      - name: sample-app
        image: nginx:1.27
        ports:
        - containerPort: 80
EOT
}
