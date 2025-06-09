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
  config_path = "/home/nataliagranato/Downloads/platform-locals/terraform/010-kubernetes-cluster/kubeconfig"
}

provider "helm" {
  kubernetes {
    config_path = "/home/nataliagranato/Downloads/platform-locals/terraform/010-kubernetes-cluster/kubeconfig"
  }
}

provider "vault" {
  address = "https://10.191.1.2:8200"
  # token   = "<REMOVED_SECRET>"

  skip_tls_verify = true
}
