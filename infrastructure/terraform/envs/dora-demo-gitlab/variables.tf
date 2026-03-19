variable "gitlab_token" {
  type      = string
  sensitive = true
}

variable "group_name" {
  type    = string
  default = "hape-dora-sandbox"
}

variable "group_path" {
  type    = string
  default = "hape-dora-sandbox"
}

variable "subgroup_name" {
  type    = string
  default = "gitlab-free"
}

variable "subgroup_path" {
  type    = string
  default = "gitlab-free"
}

variable "default_branch" {
  type    = string
  default = "main"
}

variable "project_names" {
  type = list(string)
  default = [
    "service-a",
    "service-b",
    "service-c"
  ]
}

variable "sample_ci_content" {
  type = string
  default = <<-EOT
stages:
  - test
  - deploy

unit-test:
  stage: test
  script:
    - echo "run tests"

deploy-prod:
  stage: deploy
  script:
    - echo "deploy to kind"
  only:
    - main
EOT
}

variable "sample_manifest_content" {
  type = string
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
