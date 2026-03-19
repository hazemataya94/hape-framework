terraform {
  required_providers {
    github = {
      source = "integrations/github"
    }
  }
}

variable "repositories" {
  type = list(string)
}

variable "sample_ci_content" {
  type = string
}

variable "sample_manifest_content" {
  type = string
}

variable "manifest_name_placeholder" {
  type    = string
  default = "sample-app"
}

variable "default_branch" {
  type    = string
  default = "main"
}

locals {
  repositories_set = toset(var.repositories)
}

resource "github_repository_file" "ci_file" {
  for_each            = local.repositories_set
  repository          = each.value
  branch              = var.default_branch
  file                = ".github/workflows/deploy.yml"
  content             = var.sample_ci_content
  commit_message      = "Add DORA test GitHub Actions workflow"
  overwrite_on_create = true
}

resource "github_repository_file" "manifest_file" {
  for_each            = local.repositories_set
  repository          = each.value
  branch              = var.default_branch
  file                = "kubernetes/deployment.yaml"
  content             = replace(var.sample_manifest_content, var.manifest_name_placeholder, lower(each.value))
  commit_message      = "Add sample Kubernetes manifest"
  overwrite_on_create = true
  depends_on          = [github_repository_file.ci_file]
}
