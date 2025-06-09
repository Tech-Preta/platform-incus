variable "networks" {
  description = "Incus networks."
  type = list(object({
    name    = string
    project = string
    type    = string
    config  = map(string)
  }))
}

variable "uplink_networks" {
  description = "Uplink networks configuration (like lxdbr0)."
  type = list(object({
    name   = string
    config = map(string)
  }))
  default = []
}

locals {
  networks        = { for network in var.networks : network.name => network }
  uplink_networks = { for network in var.uplink_networks : network.name => network }
}

resource "incus_network" "this" {
  for_each = local.networks

  name    = each.key
  project = try(incus_project.this[each.value.project].name, "default")
  type    = each.value.type

  config = each.value.config
}

# Manage uplink networks (like lxdbr0)
resource "incus_network" "uplink" {
  for_each = local.uplink_networks

  name   = each.key
  type   = "bridge"
  config = each.value.config
}
