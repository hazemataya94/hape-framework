terraform {
  required_providers {
    gitlab = {
      source = "gitlabhq/gitlab"
    }
  }
}

variable "group_name" {
  type = string
}

variable "group_path" {
  type = string
}

variable "subgroup_name" {
  type    = string
  default = ""
}

variable "subgroup_path" {
  type    = string
  default = ""
}

resource "gitlab_group" "root" {
  name = var.group_name
  path = var.group_path
}

resource "gitlab_group" "subgroup" {
  count     = var.subgroup_name != "" && var.subgroup_path != "" ? 1 : 0
  name      = var.subgroup_name
  path      = var.subgroup_path
  parent_id = gitlab_group.root.id
}

output "group_id" {
  value = gitlab_group.root.id
}

output "target_parent_id" {
  value = length(gitlab_group.subgroup) > 0 ? gitlab_group.subgroup[0].id : gitlab_group.root.id
}
