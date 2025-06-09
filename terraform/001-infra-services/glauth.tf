variable "glauth_config" {
  type = object({
    replicas         = optional(number, 1)
    version          = optional(string, "v2.4.0")
    profile          = optional(string, "infra-unified-1-1-20")
    load_balancer_ip = optional(string, "10.191.1.100")
    server = object({
      ldap_port  = optional(number, 3893)
      ldaps_port = optional(number, 3894)
      tracing_config = optional(object({
        enabled = optional(bool, false)
      }), {})
      backend_config = optional(object({
        base_dn = string
        legacy  = optional(bool, false)
      }))
      users = optional(list(object({
        name         = string
        uid          = number
        primary_gid  = number
        login_shell  = optional(string, "/bin/bash")
        pass_sha_256 = string
        capabilities = optional(list(object({
          action = string
          object = string
        })), [])
      })), [])
      groups = optional(list(object({
        name = string
        gid  = string
        capabilities = optional(list(object({
          action = string
          object = string
        })), [])
      })), [])
    })
  })
}

locals {
  config_file = templatefile("./templates/glauth/config.cfg.tpl", var.glauth_config.server)
  glauth_cloudinit = templatefile("./templates/glauth/cloud-init.yaml.tpl", {
    config_file = base64encode(local.config_file)
    version     = var.glauth_config.version
    certs = [
      {
        name        = "key.pem",
        permissions = "0600"
        pem         = base64encode(tls_private_key.glauth.private_key_pem)
      },
      {
        name        = "crt.pem",
        permissions = "0644"
        pem         = base64encode(tls_self_signed_cert.glauth.cert_pem)
      }
    ]
  })
}

data "cloudinit_config" "glauth" {
  gzip          = false
  base64_encode = false

  part {
    filename     = "cloud-config.yaml"
    content_type = "text/cloud-config"
    merge_type   = "list(append)+dict(recurse_array)+str()"

    content = local.glauth_cloudinit
  }
}

resource "tls_private_key" "glauth" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "tls_self_signed_cert" "glauth" {
  private_key_pem       = tls_private_key.glauth.private_key_pem
  ip_addresses          = ["127.0.0.1", var.glauth_config.load_balancer_ip]
  allowed_uses          = ["client_auth", "server_auth"]
  validity_period_hours = 24 * 365

  subject {
    common_name = var.glauth_config.load_balancer_ip
  }
}

resource "incus_instance" "glauth" {
  count = var.glauth_config.replicas

  name     = "ldap-0${count.index + 1}"
  image    = local.ubuntu_24_04_cloud
  project  = var.project
  profiles = [var.glauth_config.profile]

  config = {
    "cloud-init.user-data" : data.cloudinit_config.glauth.rendered
  }
}

resource "incus_network_lb" "glauth" {
  network        = "infra-unified"
  listen_address = var.glauth_config.load_balancer_ip

  depends_on = [incus_instance.glauth]

  backend {
    name           = "ldap-01-3893-tcp"
    target_address = incus_instance.glauth[0].ipv4_address
    target_port    = "3893"
  }

  backend {
    name           = "ldap-01-3894-tcp"
    target_address = incus_instance.glauth[0].ipv4_address
    target_port    = "3894"
  }

  port {
    listen_port    = "3894"
    target_backend = ["ldap-01-3894-tcp"]
    protocol       = "tcp"
  }

  port {
    listen_port    = "3893"
    target_backend = ["ldap-01-3893-tcp"]
    protocol       = "tcp"
  }
}
