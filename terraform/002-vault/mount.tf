resource "vault_mount" "guest" {
  type = "kv-v2"
  path = "guest"
}

resource "vault_mount" "core" {
  type = "kv-v2"
  path = "core"
}

resource "vault_kv_secret_v2" "environment" {
  mount = vault_mount.core.path
  name  = "environment"

  data_json = jsonencode({
    VAULT_ADDR = "https://${var.vault_config.load_balancer_ip}:8200"
    LDAP_URL   = var.ldap_config.url
  })

  delete_all_versions = true
}
