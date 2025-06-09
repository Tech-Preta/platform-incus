terraform {
  required_version = "~> 1.12.0"
  required_providers {
    vault = {
      source  = "hashicorp/vault"
      version = "~> 3.25.0"
    }
  }
}

provider "vault" {
  address         = "https://10.191.1.101:8200"
  skip_tls_verify = true
  token           = var.vault_token
}
