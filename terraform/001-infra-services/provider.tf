terraform {
  required_version = "~> 1.12.0"
  required_providers {
    incus = {
      source  = "lxc/incus"
      version = "0.3.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "4.1.0"
    }
    cloudinit = {
      source  = "hashicorp/cloudinit"
      version = "2.3.6"
    }
  }
}

provider "incus" {
  accept_remote_certificate = true
}
