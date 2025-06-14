terraform {
  required_version = "~> 1.9.3" # Downgraded to ensure compatibility with legacy modules. Consider centralizing this constraint if used across multiple files.
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
  config_path = "../010-kubernetes-cluster/kubeconfig"
}

provider "helm" {
  kubernetes {
    config_path = "../010-kubernetes-cluster/kubeconfig"
  }
}
