# Example skeleton — replace with your cloud provider modules, remote state, and secrets.

terraform {
  required_version = ">= 1.6.0"
}

variable "environment" {
  type    = string
  default = "staging"
}

output "note" {
  value = "Wire managed Postgres, Redis, secrets, and container hosting (ECS/AKS/GKE/Cloud Run) here."
}
