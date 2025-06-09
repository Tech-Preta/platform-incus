variable "project" {
  description = "Incus project"
  type        = string
}

variable "vault_token" {
  description = "Token de acesso ao Vault"
  type        = string
  sensitive   = true
}

variable "ldap_config" {
  description = "Configuração do LDAP"
  type = object({
    url          = string
    binddn       = string
    bindpass     = string
    userdn       = string
    userattr     = string
    groupdn      = string
    groupattr    = string
    insecure_tls = bool
  })
}

variable "vault_config" {
  description = "Configuração do Vault"
  type = object({
    profile          = string
    common_name      = string
    load_balancer_ip = string
  })
} 