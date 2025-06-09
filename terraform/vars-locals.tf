# Central locals for network configuration and service IPs
locals {
  # Network Configuration
  infra_network_cidr      = "10.191.1.0/24"
  kubernetes_network_cidr = "10.191.0.0/24"

  # Infrastructure Service IPs
  glauth_service_ip = "10.191.1.10"
  vault_service_ip  = "10.191.1.20"

  # Load Balancer IPs
  glauth_lb_ip             = "10.191.1.100"
  vault_lb_ip              = "10.191.1.101"
  kubernetes_api_lb_ip     = "10.191.0.100"
  kubernetes_ingress_lb_ip = "10.191.0.110"

  # MetalLB IP Ranges
  metallb_infra_range = "10.191.1.100-10.191.1.120"
  metallb_k8s_range   = "10.191.0.121-10.191.0.140"
}
