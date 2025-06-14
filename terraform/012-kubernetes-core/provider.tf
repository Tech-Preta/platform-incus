terraform {
  required_version = "~> 1.12.0"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.37.1"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "2.17.0"
    }
    vault = {
      source  = "hashicorp/vault"
      version = "5.0.0"
    }
  }
}

provider "kubernetes" {
  config_path = var.kubernetes_config_path
}

provider "helm" {
  kubernetes {
    config_path = var.helm_config_path
  }
}

provider "vault" {
  address = var.vault_address
  # token   = "<REMOVED_SECRET>"

  skip_tls_verify = true
}
