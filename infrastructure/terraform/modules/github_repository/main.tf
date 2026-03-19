terraform {
  required_providers {
    github = {
      source = "integrations/github"
    }
  }
}

variable "repositories" {
  type = list(
    object(
      {
        name         = string
        description  = string
        visibility   = string
      }
    )
  )
}

resource "github_repository" "repositories" {
  for_each             = { for repository in var.repositories : repository.name => repository }
  name                 = each.value.name
  description          = each.value.description
  visibility           = each.value.visibility
  auto_init            = true
  delete_branch_on_merge = true
}

output "repository_names" {
  value = [for repository in github_repository.repositories : repository.name]
}

output "repository_node_ids" {
  value = { for key, repository in github_repository.repositories : key => repository.node_id }
}
