terraform {
  required_providers {
    gitlab = {
      source = "gitlabhq/gitlab"
    }
  }
}

variable "project_ids" {
  type = map(number)
}

variable "default_branch" {
  type    = string
  default = "main"
}

variable "sample_ci_content" {
  type = string
}

variable "sample_manifest_content" {
  type = string
}

resource "gitlab_repository_file" "ci_file" {
  for_each             = var.project_ids
  project              = each.value
  file_path            = ".gitlab-ci.yml"
  branch               = var.default_branch
  encoding             = "text"
  content              = var.sample_ci_content
  author_email         = "demo@example.com"
  author_name          = "HAPE Sandbox"
  commit_message       = "Add DORA test CI pipeline"
  overwrite_on_create  = true
}

resource "gitlab_repository_file" "manifest_file" {
  for_each             = var.project_ids
  project              = each.value
  file_path            = "kubernetes/deployment.yaml"
  branch               = var.default_branch
  encoding             = "text"
  content              = var.sample_manifest_content
  author_email         = "demo@example.com"
  author_name          = "HAPE Sandbox"
  commit_message       = "Add sample Kubernetes manifest"
  overwrite_on_create  = true
  depends_on           = [gitlab_repository_file.ci_file]
}
