variable "kubernetes_config_path" {
  description = "Path to the Kubernetes cluster configuration file."
  type        = string
  default     = "../010-kubernetes-cluster/kubeconfig"
}

variable "helm_config_path" {
  description = "Path to the Kubernetes cluster configuration file for Helm."
  type        = string
  default     = "../010-kubernetes-cluster/kubeconfig"
}

variable "vault_address" {
  description = "The address of the Vault server."
  type        = string
  default     = "https://10.191.1.2:8200"
}
