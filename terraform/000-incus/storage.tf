variable "storage_pools" {
  type = list(object({
    name   = string
    driver = string
    config = optional(map(string), {})
  }))
  default = []
}

resource "incus_storage_pool" "this" {
  for_each = { for pool in var.storage_pools : pool.name => pool }

  name   = each.value.name
  driver = each.value.driver
  config = each.value.config
}
