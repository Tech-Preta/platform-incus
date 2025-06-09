variable "external_dns_config" {
  type = object({
    namespace       = optional(string, "external-dns")
    version         = optional(string, "1.16.0")
    log_level       = optional(string, "info")
    log_format      = optional(string, "json")
    nameserver_host = optional(string)
    resources = optional(object({
      requests = optional(object({
        cpu    = optional(string, "30m")
        memory = optional(string, "128Mi")
      }), {})
      limits = optional(object({
        cpu    = optional(string, "300m")
        memory = optional(string, "512Mi")
      }), {})
    }), {})
  })
  default = {}
}

resource "kubernetes_namespace_v1" "external_dns" {
  metadata {
    name = var.external_dns_config.namespace
  }
}

resource "helm_release" "external_dns" {
  name       = local.helm_charts.external_dns.release_name
  namespace  = kubernetes_namespace_v1.external_dns.id
  chart      = local.helm_charts.external_dns.chart
  repository = local.helm_charts.external_dns.repository
  version    = var.external_dns_config.version

  values = [
    templatefile("./values/external_dns.yaml.tpl", {
      log_level       = var.external_dns_config.log_level
      log_format      = var.external_dns_config.log_format
      domain_filters  = ["nataliagranato.xyz"]
      nameserver_host = "8.8.8.8" # Using public DNS since we're not using internal DNS server
      nameserver_port = "53"
      nameserver_zone = "nataliagranato.xyz"
      tsig_keyname    = "nataliagranato.xyz."
      tsig_secret     = "" # No TSIG secret needed for public DNS
      resources       = var.external_dns_config.resources
    })
  ]
}
