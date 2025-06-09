output "glauth_ip" {
  description = "IP do GLAuth (LDAP)"
  value       = incus_network_lb.glauth.listen_address
}

output "glauth_ldap_port" {
  description = "Porta LDAP do GLAuth"
  value       = 3893
}

output "glauth_ldaps_port" {
  description = "Porta LDAPS do GLAuth"
  value       = 3894
}

output "glauth_base_dn" {
  description = "Base DN do GLAuth"
  value       = var.base_dn
}

output "glauth_users" {
  description = "Usuários do GLAuth (usuário, senha, grupo)"
  value = [
    for user in var.glauth_users : {
      name  = user.name
      dn    = "cn=${user.name},${var.base_dn}"
      pass  = user.pass
      group = user.gidnumber == 1000 ? "admin" : "guest"
    }
  ]
}

output "vault_ip" {
  description = "IP do Vault"
  value       = incus_network_lb.vault.listen_address
}

output "vault_port" {
  description = "Porta do Vault"
  value       = 8200
} 