terraform {
  required_providers {
    github = {
      source = "integrations/github"
    }
  }
}

variable "owner" {
  type = string
}

output "owner" {
  value = var.owner
}
