terraform {
  required_version = ">= 1.6.0"
  required_providers {
    gitlab = {
      source = "gitlabhq/gitlab"
    }
  }
}

provider "gitlab" {
  token    = var.gitlab_token
  base_url = "https://gitlab.com/api/v4/"
}

locals {
  project_objects = [
    for project_name in var.project_names : {
      name           = project_name
      path           = lower(replace(project_name, " ", "-"))
      default_branch = var.default_branch
    }
  ]
}

module "gitlab_group" {
  source        = "../../modules/gitlab_group"
  group_name    = var.group_name
  group_path    = var.group_path
  subgroup_name = var.subgroup_name
  subgroup_path = var.subgroup_path
}

module "gitlab_project" {
  source          = "../../modules/gitlab_project"
  parent_group_id = module.gitlab_group.target_parent_id
  projects        = local.project_objects
}

module "gitlab_repository_files" {
  source                  = "../../modules/gitlab_repository_files"
  project_ids             = module.gitlab_project.project_ids
  default_branch          = var.default_branch
  sample_ci_content       = var.sample_ci_content
  sample_manifest_content = var.sample_manifest_content
}
