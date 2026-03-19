terraform {
  required_providers {
    gitlab = {
      source = "gitlabhq/gitlab"
    }
  }
}

variable "parent_group_id" {
  type = number
}

variable "projects" {
  type = list(object({ name = string, path = string, default_branch = string }))
}

resource "gitlab_project" "projects" {
  for_each         = { for project in var.projects : project.path => project }
  name             = each.value.name
  path             = each.value.path
  namespace_id     = var.parent_group_id
  default_branch   = each.value.default_branch
  initialize_with_readme = true
}

output "project_ids" {
  value = { for key, item in gitlab_project.projects : key => item.id }
}
