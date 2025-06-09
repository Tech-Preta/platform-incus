variable "metallb_config" {
  type = object({
    namespace       = optional(string, "metallb-system")
    ip_address_pool = optional(list(string), [])
  })
  default = {}
}

resource "kubernetes_namespace_v1" "metallb" {
  metadata {
    name = var.metallb_config.namespace
  }
}

resource "null_resource" "metallb_native_manifest" {
  provisioner "local-exec" {
    command = <<EOT
set -e
echo "Applying MetalLB native manifest..."
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.15.2/config/manifests/metallb-native.yaml --namespace=${var.metallb_config.namespace}

echo "Verifying CRD creation..."
kubectl get crd ipaddresspools.metallb.io > /dev/null || (echo "CRD ipaddresspools.metallb.io not found after apply!" && exit 1)
kubectl get crd l2advertisements.metallb.io > /dev/null || (echo "CRD l2advertisements.metallb.io not found after apply!" && exit 1)
kubectl get crd bgppeers.metallb.io > /dev/null || (echo "CRD bgppeers.metallb.io not found after apply!" && exit 1)
kubectl get crd bfdprofiles.metallb.io > /dev/null || (echo "CRD bfdprofiles.metallb.io not found after apply!" && exit 1)
kubectl get crd bgpadvertisements.metallb.io > /dev/null || (echo "CRD bgpadvertisements.metallb.io not found after apply!" && exit 1)
kubectl get crd communities.metallb.io > /dev/null || (echo "CRD communities.metallb.io not found after apply!" && exit 1)
echo "Initial CRD get successful."

echo "Waiting for MetalLB CRDs to be established..."
kubectl wait --for=condition=established --timeout=180s crd/ipaddresspools.metallb.io
kubectl wait --for=condition=established --timeout=180s crd/l2advertisements.metallb.io
kubectl wait --for=condition=established --timeout=180s crd/bgppeers.metallb.io
kubectl wait --for=condition=established --timeout=180s crd/bfdprofiles.metallb.io
kubectl wait --for=condition=established --timeout=180s crd/bgpadvertisements.metallb.io
kubectl wait --for=condition=established --timeout=180s crd/communities.metallb.io
echo "MetalLB CRDs established."

echo "Verifying API server recognizes IPAddressPool CRD..."
timeout_api_check=90
interval_api_check=5
end_time_api_check=$(( $(date +%s) + timeout_api_check ))
while ! kubectl api-resources --api-group=metallb.io | grep -q -w ipaddresspools; do
  if [[ $(date +%s) -gt $end_time_api_check ]]; then
    echo "Error: Timeout waiting for API server to recognize IPAddressPool CRD."
    echo "Attempting to list CRDs from metallb.io group:"
    kubectl api-resources --api-group=metallb.io
    exit 1
  fi
  echo "IPAddressPool CRD not yet recognized by API server (metallb.io group), retrying in $${interval_api_check} seconds..."
  sleep $${interval_api_check}
done
echo "API server recognizes IPAddressPool CRD."

echo "Attempting a dry-run creation of a dummy IPAddressPool to confirm GVK recognition (will retry)..."
max_dry_run_attempts=5
dry_run_attempt=0
dry_run_successful=false
while [ $dry_run_attempt -lt $max_dry_run_attempts ]; do
  echo "Dry-run attempt $(($dry_run_attempt + 1)) of $max_dry_run_attempts..."
  cat <<EOF_DRY_RUN | kubectl apply --namespace=${var.metallb_config.namespace} --dry-run=server -f -
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: dummy-pool-dryrun-attempt-$(($dry_run_attempt + 1))
spec:
  addresses:
    - 192.168.200.200/32 # Dummy IP, won\'t be used
EOF_DRY_RUN

  if [ $? -eq 0 ]; then
    dry_run_successful=true
    echo "Dry-run creation of dummy IPAddressPool successful."
    break
  else
    echo "Dry-run attempt $(($dry_run_attempt + 1)) failed. Retrying in 10 seconds..."
    sleep 10
  fi
  dry_run_attempt=$(($dry_run_attempt + 1))
done

if [ "$dry_run_successful" = false ]; then
  echo "Error: Dry-run creation of dummy IPAddressPool failed after $max_dry_run_attempts attempts. GVK might not be fully ready or webhook is unhealthy."
  echo "Attempting to list API resources for metallb.io again:"
  kubectl api-resources --api-group=metallb.io
  echo "Describing MetalLB controller pods:"
  kubectl describe pods -n ${var.metallb_config.namespace} -l app=metallb,component=controller
  echo "Logs from MetalLB controller webhook container:"
  kubectl logs -n ${var.metallb_config.namespace} -l app=metallb,component=controller --tail=50 # Ajuste --tail conforme necessário
  exit 1
fi

echo "Giving K8s API server an additional moment..."
sleep 10 # Sleep pode ser ajustado ou removido se o dry-run for suficiente

echo "Waiting for memberlist secret to be created..."
timeout_seconds=180
interval_seconds=5
end_time=$(( $(date +%s) + timeout_seconds ))
while ! kubectl get secret memberlist --namespace=${var.metallb_config.namespace} -o name > /dev/null 2>&1; do
  if [[ $(date +%s) -gt $end_time ]]; then
    echo "Error: Timeout waiting for memberlist secret in namespace ${var.metallb_config.namespace}."
    exit 1
  fi
  echo "memberlist secret not yet found, retrying in $${interval_seconds} seconds..."
  sleep $${interval_seconds}
done
echo "memberlist secret found."

echo "Waiting for MetalLB controller deployment to be available..."
kubectl wait deployment/controller --namespace=${var.metallb_config.namespace} --for=condition=Available --timeout=180s
echo "MetalLB controller deployment available."

echo "MetalLB native manifest applied and key resources are ready."
EOT
  }
  triggers = {
    always_run = timestamp()
  }
  depends_on = [kubernetes_namespace_v1.metallb]
}

resource "kubernetes_manifest" "metallb_ipaddresspool" {
  manifest = {
    apiVersion = "metallb.io/v1beta1"
    kind       = "IPAddressPool"
    metadata = {
      name      = "lb-pool"
      namespace = kubernetes_namespace_v1.metallb.id
    }
    spec = {
      addresses = ["10.191.0.121-10.191.0.140"]
    }
  }
  depends_on = [null_resource.metallb_native_manifest]
}

resource "kubernetes_manifest" "metallb_l2advertisement" {
  manifest = {
    apiVersion = "metallb.io/v1beta1"
    kind       = "L2Advertisement"
    metadata = {
      name      = "lb-pool-advertisement"
      namespace = kubernetes_namespace_v1.metallb.id
    }
    spec = {
      ipAddressPools = ["lb-pool"]
    }
  }
  depends_on = [kubernetes_manifest.metallb_ipaddresspool]
}
