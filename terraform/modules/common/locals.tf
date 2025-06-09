variable "project" {
  description = "Incus project"
  default     = "default"
  type        = string
}

locals {
  bare_metal = {
    peter = {
      ipv4 = "10.220.0.250"
    }
  }
  endpoints = {
    kubernetes = {
      apps = "10.191.0.99" # Updated to match the actual load balancer IP
    }
  }
  zones = {
    root    = "nataliagranato.xyz."
    project = "apps.nataliagranato.xyz."
  }
  vault = {
    core_mount = "core"
    address    = "https://vault.nataliagranato.xyz:8200"
    pki = {
      mount              = "pki"
      intermediate_mount = "pki-intermediate"
      root_ca = {
        issuer_name = "nataliagranato-root"
        common_name = "Tech Preta Vault Root CA"
        ttl         = "86400"
      }
      intermediate_ca = {
        common_name = "Tech Preta Vault Intermediate CA"
        ttl         = "86400"
      }
    }
  }
  # kubernetes = {
  #   ingress = {
  #     internal = {
  #       load_balancer_ip = "10.191.0.120"
  #     }
  #   }
  # }
}
