# Provisionamento de Componentes Core do Kubernetes (012-kubernetes-core)

Este módulo Terraform é responsável por provisionar os componentes essenciais ("core") sobre um cluster Kubernetes existente. Estes componentes incluem a CNI (Container Network Interface), balanceamento de carga para serviços, gerenciamento de certificados, DNS, armazenamento e outros utilitários fundamentais.

## Pré-requisitos

Antes de aplicar os recursos deste módulo, certifique-se de que:
1.  Um cluster Kubernetes básico esteja provisionado e acessível. Normalmente, isso é feito através do módulo `010-kubernetes-cluster`.
2.  O `kubectl` esteja configurado para apontar para o cluster correto.
3.  O Terraform esteja inicializado no diretório `012-kubernetes-core`.

## Ordem de Provisionamento e Componentes

É crucial seguir uma ordem específica ao provisionar estes componentes devido às suas dependências. A ordem recomendada é:

### 1. Cilium (CNI)

*   **Arquivo:** `cilium.tf`
*   **Descrição:** Cilium é a Interface de Rede de Contêiner (CNI) escolhida, responsável pela rede dos pods, aplicação de políticas de rede e, como configurado neste projeto, substituição do kube-proxy para gerenciamento de serviços.
*   **Aplicação:** Deve ser o primeiro componente a ser aplicado, pois a rede é fundamental para todos os outros pods e serviços no cluster.
    ```bash
    terraform apply -target=helm_release.cilium
    ```
    Aguarde a completa inicialização e estabilização dos pods do Cilium (agentes em todos os nós e operador) antes de prosseguir. Verifique os logs para confirmar que não há erros e que o `kubeProxyReplacement` está ativo.

### 2. MetalLB (Load Balancer)

*   **Arquivo:** `metallb.tf`
*   **Descrição:** MetalLB fornece uma implementação de balanceador de carga de rede para clusters Kubernetes que não rodam em provedores de nuvem com LBaaS nativo. Ele permite expor serviços do tipo `LoadBalancer`. Este módulo configura o MetalLB em modo L2, incluindo:
    *   Instalação dos manifestos do MetalLB (`null_resource.metallb_native_manifest`).
    *   Criação de `IPAddressPool` (`kubernetes_manifest.metallb_ipaddresspool`) para definir o range de IPs disponíveis para os LoadBalancers.
    *   Criação de `L2Advertisement` (`kubernetes_manifest.metallb_l2advertisement`) para anunciar os IPs dos serviços na rede local.
*   **Aplicação:** Deve ser aplicado após o Cilium estar funcional e estável, pois os pods do MetalLB (controller e speakers) precisam de conectividade de rede e o correto funcionamento do service routing (agora gerenciado pelo Cilium).
    ```bash
    # Aplicar o manifesto base do MetalLB e aguardar CRDs e controller
    terraform apply -target=null_resource.metallb_native_manifest
    # Após o null_resource concluir com sucesso (verificar logs do script), aplicar os CRs:
    terraform apply -target=kubernetes_manifest.metallb_ipaddresspool
    terraform apply -target=kubernetes_manifest.metallb_l2advertisement
    ```
    Verifique se os pods do MetalLB (controller e speakers) estão rodando, se o `IPAddressPool` e `L2Advertisement` foram criados corretamente e se os speakers não apresentam erros de conexão com a API.

### 3. Demais Componentes Core

Após Cilium e MetalLB estarem operacionais e validados, os seguintes componentes podem ser provisionados. Eles podem geralmente ser aplicados juntos ou em qualquer ordem entre si, a menos que haja dependências específicas não listadas aqui.

*   **Cert-Manager**
    *   **Arquivo:** `cert_manager.tf`
    *   **Descrição:** Gerencia automaticamente a emissão e renovação de certificados TLS no Kubernetes. É crucial para proteger Ingresses e outros serviços.
    *   **Recurso Terraform:** `helm_release.cert_manager`

*   **CoreDNS (Customizações)**
    *   **Arquivo:** `coredns.tf`
    *   **Descrição:** Aplica customizações ao CoreDNS, o servidor DNS padrão do cluster. (Nota: Cilium também possui funcionalidades DNS que podem interagir ou complementar o CoreDNS).
    *   **Recurso Terraform:** `helm_release.coredns` (ou o recurso específico definido em `coredns.tf`)

*   **CSI - Local Path Provisioner**
    *   **Arquivo:** `csi.tf`
    *   **Descrição:** Provisiona o Local Path Provisioner, que fornece armazenamento persistente utilizando o armazenamento local dos nós.
    *   **Recurso Terraform:** `helm_release.local_path_provisioner`

*   **ExternalDNS**
    *   **Arquivo:** `external_dns.tf`
    *   **Descrição:** Sincroniza os Services e Ingresses do Kubernetes com provedores de DNS, automatizando a criação de registros DNS.
    *   **Recurso Terraform:** `helm_release.external_dns`

*   **Metrics Server**
    *   **Arquivo:** `metrics_server.tf`
    *   **Descrição:** Coleta métricas de uso de recursos dos nós e pods, essenciais para o Horizontal Pod Autoscaler (HPA) e para o `kubectl top`.
    *   **Recurso Terraform:** `helm_release.metrics_server`

*   **Traefik (Ingress Controller)**
    *   **Arquivo:** `traefik.tf`
    *   **Descrição:** Traefik é um Ingress Controller moderno que gerencia o acesso externo aos serviços no cluster. Ele utilizará um IP do MetalLB para seu serviço do tipo `LoadBalancer`.
    *   **Recurso Terraform:** `helm_release.traefik`

*   **Aplicação dos demais componentes:**
    Após Cilium e MetalLB, você pode aplicar todos os outros de uma vez:
    ```bash
    terraform apply
    ```
    Ou individualmente, se preferir, usando `-target` (exemplo para Traefik):
    ```bash
    terraform apply -target=helm_release.traefik
    ```

## Ordem de Provisionamento para 012-kubernetes-core

Ao provisionar os componentes do Kubernetes Core definidos neste diretório (`012-kubernetes-core`), é crucial seguir uma ordem específica para garantir a correta configuração e funcionamento dos serviços. A ordem recomendada é a seguinte:

1.  **Cilium (CNI e Kube-Proxy Replacement)**:
    *   Primeiro, aplique a configuração do Cilium. Isso instalará o CNI (Container Network Interface) e, se configurado (como no estado atual), substituirá o `kube-proxy`.
    *   Comando Terraform: `terraform apply -target=helm_release.cilium`
    *   Verifique se todos os pods do Cilium estão em execução no namespace `kube-system` antes de prosseguir.

2.  **MetalLB (Load Balancer)**:
    *   Após o Cilium estar operacional, instale o MetalLB.
    *   Comando Terraform para a manifestação nativa (método atual): `terraform apply -target=null_resource.metallb_native_manifest`
    *   Em seguida, crie os recursos customizados (CRDs) do MetalLB para definir os pools de IPs e os anúncios L2.
    *   Comandos Terraform:
        *   `terraform apply -target=kubernetes_manifest.metallb_ipaddresspool`
        *   `terraform apply -target=kubernetes_manifest.metallb_l2advertisement`
    *   Verifique se os pods do MetalLB estão em execução no namespace `metallb-system` e se os CRDs foram criados corretamente.

3.  **Restante dos Componentes Core**:
    *   Com a rede e o balanceador de carga configurados, os demais componentes core podem ser provisionados. Isso inclui, mas não se limita a:
        *   Cert-Manager
        *   Traefik (Ingress Controller)
        *   CoreDNS (se houver customizações além do padrão do RKE2/Cilium)
        *   Metrics Server
        *   CSI Drivers (como o `local-path-provisioner`)
        *   ExternalDNS
    *   Esses componentes podem geralmente ser aplicados juntos ou em uma ordem que faça sentido para suas dependências (por exemplo, Cert-Manager antes de componentes que solicitam certificados).
    *   Comando Terraform para aplicar todos os demais (ou individualmente com `-target`): `terraform apply` (após os passos 1 e 2 terem sido concluídos e seus estados salvos).

**Exemplo de fluxo de provisionamento inicial completo:**

```bash
# 1. Provisionar Cilium
terraform apply -target=helm_release.cilium

# Aguardar pods do Cilium ficarem prontos

# 2. Provisionar MetalLB (manifesto e CRDs)
terraform apply -target=null_resource.metallb_native_manifest
terraform apply -target=kubernetes_manifest.metallb_ipaddresspool
terraform apply -target=kubernetes_manifest.metallb_l2advertisement

# Aguardar pods do MetalLB ficarem prontos e CRDs serem reconhecidos

# 3. Provisionar o restante dos componentes
terraform apply -target=helm_release.cert_manager # Exemplo
terraform apply -target=helm_release.traefik     # Exemplo
# ... e assim por diante para outros componentes, ou:
terraform apply # Para aplicar tudo o que falta

```

Seguir esta ordem ajuda a evitar problemas de dependência, especialmente relacionados à rede e à atribuição de IPs para serviços do tipo `LoadBalancer`.

## Considerações Finais

*   Sempre verifique os logs dos pods (`kubectl logs <pod-name> -n <namespace>`) após cada aplicação para garantir que os componentes foram iniciados corretamente e estão saudáveis.
*   Consulte os arquivos `values/<componente>.yaml.tpl` para entender as configurações padrão de cada chart Helm e como customizá-las através das variáveis no `terraform.tfvars` ou `vars-locals.tf`.
*   A aplicação direcionada com `-target` é útil para instalação inicial controlada ou para recuperação de erros, mas para atualizações subsequentes, um `terraform apply` completo (após `terraform plan`) é geralmente preferido para gerenciar o estado de todos os recursos.
