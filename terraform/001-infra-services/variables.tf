variable "project" {
  description = "Nome do projeto Incus"
  type        = string
  default     = "infra"
}

variable "base_dn" {
  description = "Base DN do GLAuth"
  type        = string
}

variable "glauth_users" {
  description = "Lista de usuários do GLAuth"
  type = list(object({
    name      = string
    pass      = string
    gidnumber = number
  }))
} 