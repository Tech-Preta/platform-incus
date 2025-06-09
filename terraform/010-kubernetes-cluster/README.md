# Kubernetes Cluster

Este projeto é responsável por provisionar e instalar/configurar um cluster Kubernetes no Incus usando RKE2, com configuração simplificada sem dependências de DNS.

## Stack

- RKE2
- Incus

## Configuração

O cluster é configurado com:
- **Load Balancer**: `10.191.0.99` para acesso ao API server
- **Portas**: 6443 (Kubernetes API), 9345 (RKE2), 80 (HTTP)
- **Rede**: `kubernetes`
- **Projeto**: `apps` (configurável via `terraform.tfvars`)

## Mudanças Realizadas

### Remoção de Dependências DNS

Para simplificar o deployment, foram removidas todas as dependências de DNS:

- ❌ Removido provider `dns` do `provider.tf`
- ❌ Removido recurso `dns_a_record_set.apiserver` do `main.tf`  
- ❌ Removido output `dns` do `output.tf`
- ❌ Removida variável `apiserver_dns` do módulo `kubernetes-node`
- ✅ Configuração usando apenas IPs para comunicação

### Configuração de Rede

- **API Server Load Balancer**: `10.191.0.99`
- **TLS SAN**: Apenas o IP do load balancer
- **Bootstrap Server**: Mesmo IP do load balancer

### Correções de Infraestrutura

Para que o load balancer funcione corretamente, foi necessário atualizar a configuração de rede uplink no módulo `000-incus`:

- ✅ Adicionada rota `10.191.0.99/32` às rotas IPv4 da rede uplink `lxdbr0`
- ✅ Corrigida lógica de bootstrap no cloud-init (control plane index 0)
- ✅ Melhorado script de instalação do RKE2 com melhor tratamento de erros
- ✅ Adicionado `systemctl daemon-reload` aos templates cloud-init

### Verificação do Cluster

Para verificar se o cluster está funcionando:

```bash
# Obter kubeconfig
incus exec -p apps control-plane-<id> cat /etc/rancher/rke2/rke2.yaml > kubeconfig

# Testar conectividade
export KUBECONFIG=kubeconfig
kubectl get nodes
```

---

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name                                                                      | Version   |
| ------------------------------------------------------------------------- | --------- |
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | ~> 1.12.0 |
| <a name="requirement_incus"></a> [incus](#requirement\_incus)             | 0.3.0     |
| <a name="requirement_null"></a> [null](#requirement\_null)                | 3.2.4     |
| <a name="requirement_random"></a> [random](#requirement\_random)          | 3.7.2     |

## Providers

| Name                                                       | Version |
| ---------------------------------------------------------- | ------- |
| <a name="provider_incus"></a> [incus](#provider\_incus)    | 0.3.0   |
| <a name="provider_null"></a> [null](#provider\_null)       | 3.2.4   |
| <a name="provider_random"></a> [random](#provider\_random) | 3.7.2   |

## Modules

| Name                                                                          | Source                     | Version |
| ----------------------------------------------------------------------------- | -------------------------- | ------- |
| <a name="module_common"></a> [common](#module\_common)                        | ../modules/common          | n/a     |
| <a name="module_control_plane"></a> [control\_plane](#module\_control\_plane) | ../modules/kubernetes-node | n/a     |
| <a name="module_worker"></a> [worker](#module\_worker)                        | ../modules/kubernetes-node | n/a     |

## Resources

| Name                                                                                                                | Type     |
| ------------------------------------------------------------------------------------------------------------------- | -------- |
| [incus_network_lb.control_plane](https://registry.terraform.io/providers/lxc/incus/0.3.0/docs/resources/network_lb) | resource |
| [null_resource.kubeconfig](https://registry.terraform.io/providers/hashicorp/null/3.2.4/docs/resources/resource)    | resource |
| [null_resource.wait](https://registry.terraform.io/providers/hashicorp/null/3.2.4/docs/resources/resource)          | resource |
| [random_bytes.token](https://registry.terraform.io/providers/hashicorp/random/3.7.2/docs/resources/bytes)           | resource |

## Inputs

| Name                                                                        | Description                  | Type                                                                                                                      | Default            | Required |
| --------------------------------------------------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ------------------ | :------: |
| <a name="input_project"></a> [project](#input\_project)                     | Incus project.               | `string`                                                                                                                  | n/a                |   yes    |
| <a name="input_control_plane"></a> [control\_plane](#input\_control\_plane) | Control Plane configuration. | <pre>object({<br>    replicas = optional(number, 1)<br>    profile  = optional(string, "kubernetes-2-4-20")<br>  })</pre> | `{}`               |    no    |
| <a name="input_rke2_version"></a> [rke2\_version](#input\_rke2\_version)    | RKE2 version.                | `string`                                                                                                                  | `"v1.33.1+rke2r1"` |    no    |
| <a name="input_workers"></a> [workers](#input\_workers)                     | Workers configuration.       | <pre>object({<br>    replicas = optional(number, 2)<br>    profile  = optional(string, "kubernetes-2-4-20")<br>  })</pre> | `{}`               |    no    |

## Outputs

| Name                                                                          | Description |
| ----------------------------------------------------------------------------- | ----------- |
| <a name="output_control_plane"></a> [control\_plane](#output\_control\_plane) | n/a         |
| <a name="output_worker"></a> [worker](#output\_worker)                        | n/a         |
<!-- END_TF_DOCS -->
