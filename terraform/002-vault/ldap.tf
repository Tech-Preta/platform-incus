# Configuração do backend de autenticação LDAP
resource "vault_auth_backend" "ldap" {
  type        = "ldap"
  path        = "glauth-ldap"
  description = "LDAP authentication backend for GLAuth"
  tune {
    listing_visibility = "unauth"
    token_type         = "default-service"
  }
}

# Configuração do backend LDAP
resource "vault_ldap_auth_backend" "ldap" {
  path            = vault_auth_backend.ldap.path
  url             = var.ldap_config.url
  binddn          = var.ldap_config.binddn
  bindpass        = var.ldap_config.bindpass
  userdn          = var.ldap_config.userdn
  userattr        = var.ldap_config.userattr
  groupdn         = var.ldap_config.groupdn
  groupattr       = var.ldap_config.groupattr
  insecure_tls    = var.ldap_config.insecure_tls
  starttls        = false
  tls_min_version = "tls12"
  description     = "LDAP authentication for Vault"

  # Configurações específicas do GLAuth
  groupfilter = "(&(objectClass=groupOfUniqueNames)(uniqueMember=cn={{.Username}},ou=admin,ou=users,dc=nataliagranato,dc=xyz))"
  upndomain   = ""
  userfilter  = "(&(objectClass=posixAccount)(cn={{.Username}}))"

  depends_on = [vault_auth_backend.ldap]
}

# Configuração de auditoria
resource "vault_audit" "this" {
  type = "file"
  options = {
    file_path = "/opt/vault/audit.log"
  }
}
