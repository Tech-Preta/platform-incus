\
# Plataform on Kubernetes e Terraform

## Introdução

Este projeto utiliza Terraform para provisionar e gerenciar uma infraestrutura completa, desde a camada de virtualização básica com Incus até a orquestração de contêineres com Kubernetes e a implantação de serviços. O objetivo é criar um ambiente robusto, automatizado e escalável para hospedar aplicações.

## Tecnologias Principais Utilizadas

A infraestrutura é construída sobre um conjunto de tecnologias de código aberto e padrões da indústria:

*   **Terraform:** Ferramenta de Infraestrutura como Código (IaC) usada para definir e provisionar todos os componentes da infraestrutura de forma declarativa.
*   **Incus:** Sucessor do LXD, é um gerenciador de máquinas virtuais e contêineres de sistema. Utilizado na camada base (`000-incus`) para criar instâncias (VMs ou contêineres de sistema), redes virtuais e volumes de armazenamento que servem de fundação para os demais serviços.
*   **OVN (Open Virtual Network):** Utilizado em conjunto com o Incus para fornecer funcionalidades avançadas de rede virtual, como switches virtuais, roteadores e ACLs para as instâncias Incus.
*   **Kubernetes (K8s) - RKE2:** Plataforma de orquestração de contêineres líder de mercado. Especificamente, este projeto utiliza RKE2 (Rancher Kubernetes Engine 2), uma distribuição Kubernetes focada em segurança e conformidade.
    *   O cluster é provisionado pelo módulo `010-kubernetes-cluster`.
    *   Componentes essenciais do cluster são gerenciados em `012-kubernetes-core`.
    *   Aplicações e serviços são implantados sobre o Kubernetes através do módulo `013-kubernetes-services`.
*   **Vault (HashiCorp):** Solução para gerenciamento centralizado e seguro de segredos (tokens, senhas, certificados, chaves de API).
    *   Uma instância do Vault é provisionada como um serviço de infraestrutura em `001-infra-services` (provavelmente em instâncias Incus).
    *   Configurações específicas do Vault, como métodos de autenticação (ex: LDAP), engines de segredos e políticas, são gerenciadas em `002-vault`.
    *   Há indícios de uma possível implantação do Vault também sobre Kubernetes em `013-kubernetes-services`.
*   **GLAuth:** Servidor LDAP leve, provavelmente utilizado para fornecer autenticação centralizada para usuários e serviços dentro da infraestrutura (configurado em `001-infra-services`).
*   **Cilium:** Interface de Rede de Contêiner (CNI) para Kubernetes, oferecendo rede, observabilidade e segurança. Configurado em `012-kubernetes-core`, possivelmente substituindo o kube-proxy e fornecendo políticas de rede avançadas.
*   **MetalLB:** Implementação de balanceador de carga para clusters Kubernetes em ambientes bare-metal (ou que não possuem um provedor de nuvem com LBaaS nativo). Permite expor serviços do tipo `LoadBalancer`. Configurado em `012-kubernetes-core`.
*   **Traefik:** Ingress controller nativo para a nuvem que gerencia o tráfego de entrada para os serviços Kubernetes.
    *   Suas Custom Resource Definitions (CRDs) são instaladas em `011-kubernetes-crds`.
    *   A implantação e configuração do Traefik ocorrem em `012-kubernetes-core`.
*   **Cert-Manager:** Automatiza o gerenciamento e a emissão de certificados TLS no Kubernetes. Configurado em `012-kubernetes-core` para proteger os endpoints expostos.
*   **CoreDNS:** Servidor DNS para o cluster Kubernetes, responsável pela descoberta de serviços internos. Customizações podem ser aplicadas em `012-kubernetes-core`.
*   **CSI (Container Storage Interface) Drivers:**
    *   `local-path-provisioner` (encontrado em `012-kubernetes-core/charts/`): Utilizado para provisionar armazenamento persistente usando diretórios no nó do host, útil para desenvolvimento ou clusters de nó único.
*   **ExternalDNS:** Sincroniza os serviços Kubernetes expostos e Ingresses com provedores de DNS, automatizando a criação de registros DNS. Configurado em `012-kubernetes-core`.
*   **Metrics Server:** Coleta métricas de uso de recursos dos pods e nós no Kubernetes, essencial para o Horizontal Pod Autoscaler (HPA). Configurado em `012-kubernetes-core`.
*   **Kube Prometheus Stack:** (Inferido a partir de `011-kubernetes-crds/kube_prometheus.tf`) Solução de monitoramento completa para Kubernetes, incluindo Prometheus para coleta de métricas, Grafana para visualização e Alertmanager para alertas.

## Estrutura de Diretórios do Projeto

O projeto Terraform está organizado em módulos numerados, refletindo uma progressão lógica no provisionamento da infraestrutura:

*   `README.md` (este arquivo): Documentação geral do projeto.
*   `vars-global.tf`, `vars-locals.tf`: Definições de variáveis globais e locais usadas em todo o projeto.
*   `000-incus/`: Provisionamento da infraestrutura base com Incus. Isso inclui a criação de projetos Incus, redes virtuais (possivelmente com OVN), perfis de instância e volumes de armazenamento.
*   `001-infra-services/`: Implantação de serviços de infraestrutura essenciais sobre as instâncias Incus. Exemplos incluem GLAuth (LDAP) e uma instância primária do HashiCorp Vault.
*   `002-vault/`: Configuração detalhada da instância do Vault provisionada anteriormente, incluindo a configuração de métodos de autenticação, engines de segredos, políticas de acesso e integração com outros serviços.
*   `010-kubernetes-cluster/`: Criação do cluster Kubernetes. Este módulo é responsável por configurar e iniciar os nós do control plane e os worker nodes.
*   `011-kubernetes-crds/`: Instalação de Custom Resource Definitions (CRDs) no cluster Kubernetes. CRDs são extensões da API do Kubernetes necessárias para o funcionamento de certos componentes, como Traefik e Prometheus.
*   `012-kubernetes-core/`: Implantação e configuração dos componentes centrais e de suporte do Kubernetes. Isso inclui CNI (Cilium), balanceador de carga (MetalLB), ingress controller (Traefik), gerenciamento de certificados (Cert-Manager), DNS (CoreDNS), provisionadores de armazenamento (CSI), ExternalDNS e Metrics Server.
*   `013-kubernetes-services/`: Implantação de aplicações e serviços de usuário final sobre o cluster Kubernetes. Um exemplo aqui é a possível implantação do Vault como um serviço dentro do Kubernetes.
*   `modules/`: Contém módulos Terraform reutilizáveis que encapsulam lógicas comuns, como a criação de nós Kubernetes (`kubernetes-node`) ou a aplicação de manifestos Kubernetes brutos (`raw-kubernetes-manifest`).

## Fluxo de Provisionamento Geral (Alto Nível)

A infraestrutura é tipicamente provisionada na seguinte ordem:

1.  **Configuração da Base Incus (`000-incus`):** Criação do ambiente de virtualização fundamental.
2.  **Serviços de Infraestrutura (`001-infra-services`):** Implantação de serviços como Vault e GLAuth nas instâncias Incus.
3.  **Configuração do Vault (`002-vault`):** Detalhamento da configuração do Vault.
4.  **Cluster Kubernetes (`010-kubernetes-cluster`):** Provisionamento dos nós do Kubernetes.
5.  **Instalação de CRDs (`011-kubernetes-crds`):** Preparação do cluster com as definições de recursos customizados.
6.  **Componentes Core do Kubernetes (`012-kubernetes-core`):** Habilitação da rede, balanceamento de carga, ingresso e outros serviços essenciais no cluster.
7.  **Aplicações e Serviços no Kubernetes (`013-kubernetes-services`):** Implantação das cargas de trabalho finais.

Este fluxo garante que as dependências entre os diferentes componentes da infraestrutura sejam respeitadas.
