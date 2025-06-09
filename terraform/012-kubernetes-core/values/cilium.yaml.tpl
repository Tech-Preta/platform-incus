k8sServiceHost: ${apiserver_endpoint}
k8sServicePort: "6443"

# Use VXLAN tunnel mode for maximum compatibility
routingMode: tunnel
tunnelProtocol: vxlan

# Conservative networking settings
ipam:
  mode: kubernetes

# Disable ALL eBPF features to avoid compilation issues
bpf:
  masquerade: false
  lbMap:
    max: 65536
  ctTcpMax: 524288
  ctAnyMax: 262144

# Enable kube-proxy replacement
kubeProxyReplacement: true

# Disable advanced features
envoy:
  enabled: false
l7Proxy: false
encryption:
  enabled: false
hubble:
  enabled: false

# Disable datapath features that may cause eBPF compilation
datapath:
  mode: veth
  
# Disable host firewall
hostFirewall:
  enabled: false

# Disable bandwidth manager
bandwidthManager:
  enabled: false

# Disable socket LB
socketLB:
  enabled: false

# Single operator replica
operator:
  replicas: 1
  prometheus:
    enabled: false

prometheus:
  enabled: false

# Disable features that require eBPF compilation
nodePort:
  enabled: false

# Use legacy mode for network policies
policyEnforcementMode: default

# Disable auto-generated service accounts
autoDirectNodeRoutes: false

# Logging configuration - debug as object not boolean
debug:
  enabled: false
logLevel: ${log_level}

# MTU configuration
mtu: ${mtu}
