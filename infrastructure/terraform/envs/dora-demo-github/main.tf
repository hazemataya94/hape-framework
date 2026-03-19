terraform {
  required_version = ">= 1.6.0"
  required_providers {
    github = {
      source = "integrations/github"
    }
  }
}

provider "github" {
  owner = var.github_owner
  token = var.github_token
}

locals {
  repositories = [
    for repository_name in var.repository_names : {
      name        = repository_name
      description = "DORA demo repository"
      visibility  = var.repository_visibility
    }
  ]
}

module "github_owner" {
  source = "../../modules/github_owner"
  owner  = var.github_owner
}

module "github_repository" {
  source       = "../../modules/github_repository"
  repositories = local.repositories
}

module "github_repository_files" {
  source                  = "../../modules/github_repository_files"
  repositories            = module.github_repository.repository_names
  default_branch          = var.default_branch
  sample_ci_content       = var.sample_ci_content
  sample_manifest_content = var.sample_manifest_content
}
