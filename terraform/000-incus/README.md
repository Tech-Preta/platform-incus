# Deploy do 000-incus

Este guia descreve como configurar e realizar o deploy da infraestrutura base do Incus utilizando Terraform.

## Pré-requisitos

- Incus instalado e configurado no(s) nó(s) do cluster
- Terraform instalado (~> 1.12.0)
- Permissões de administrador no Incus
- Acesso ao terminal com permissões para aplicar configurações
- OVN configurado (para redes OVN)

## Estrutura dos arquivos

- `provider.tf`: configura o provider do Incus
- `project.tf`: define projetos Incus
- `network.tf`: define redes (bridge, ovn, etc.) e gerencia uplinks
- `profile.tf`: define profiles Incus parametrizados com diferentes flavors
- `storage.tf`: gerencia storage pools do Incus
- `terraform.tfvars`: valores das variáveis (networks, profiles, projects, storage_pools, uplinks)
- `common.tf`: módulo comum compartilhado com outros módulos

## Sobre Uplinks

O uplink é a bridge que conecta as redes OVN ao ambiente externo. O uplink deve ser uma bridge gerenciada pelo Incus (ex: `lxdbr0`).

- No projeto `default`, todas as bridges gerenciadas podem ser usadas como uplink.
- Em projetos customizados, é necessário permitir explicitamente quais bridges podem ser usadas como uplink.

### Como verificar os uplinks permitidos no projeto

Execute:

```zsh
incus project show <nome-do-projeto>
```

Procure pela chave `networks.uplinks` na saída. Se não existir (caso do projeto default), todas as bridges gerenciadas estão liberadas. Se existir, apenas as bridges listadas podem ser usadas como uplink.

### Como definir uplinks permitidos em projetos customizados

```zsh
incus project set <nome-do-projeto> networks.uplinks=lxdbr0
```

Se quiser permitir mais de um uplink, separe por vírgula:

```zsh
incus project set <nome-do-projeto> networks.uplinks=lxdbr0,outra-bridge
```

## Passos para Deploy

### 1. Ajuste as variáveis

Edite o arquivo `terraform.tfvars` conforme sua topologia desejada.

#### Configuração de Storage Pools

Os storage pools são criados automaticamente pelo Terraform. Exemplo:

```hcl
storage_pools = [
  {
    name   = "default"
    driver = "btrfs"
    config = {}
  }
]
```

**Nota:** Se você já possui storage pools existentes (como "local"), pode deixar `storage_pools = []` vazio.

#### Configuração de Uplinks

Os uplinks são bridges que conectam redes OVN ao ambiente externo. Configure as rotas necessárias:

```hcl
uplinks = [
  {
    name = "lxdbr0"
    config = {
      "ipv4.routes" = "10.191.1.100/32,10.191.1.101/32"  # IPs dos load balancers
    }
  }
]
```

#### Configuração de Redes

Exemplo de rede unificada para infraestrutura:

```hcl
networks = [
  {
    name    = "infra-unified"
    project = "infra"
    type    = "ovn"
    config = {
      "ipv4.address"     = "10.191.1.1/24"
      "ipv4.dhcp.ranges" = "10.191.1.2-10.191.1.199"  # Range estendido para load balancers
      "ipv4.nat"         = "true"
      "ipv6.address"     = "none"
      "network"          = "lxdbr0"  # Uplink gerenciado pelo Incus
    }
  },
  {
    name    = "kubernetes"
    project = "apps"
    type    = "ovn"
    config = {
      "ipv4.address"     = "10.191.0.1/24"
      "ipv4.dhcp.ranges" = "10.191.0.2-10.191.0.99"
      "ipv4.nat"         = "true"
      "ipv6.address"     = "none"
      "network"          = "lxdbr0"
    }
  }
]
```

#### Configuração de Profiles

Os profiles agora suportam múltiplos flavors (combinações de CPU/memória/storage):

```hcl
profiles = [
  {
    name    = "infra-unified"
    network = "infra-unified"
    flavors = [
      {
        vcpus  = 1
        memory = 1024
        storage = {
          pool = "local"  # Use storage pool existente
          size = 20
        }
      },
      {
              {
        vcpus  = 2
        memory = 4096
        storage = {
          pool = "local"
          size = 20
        }
      }
    ]
    project = "infra"
  }
]
```

**Observações importantes:**
- Os profiles são criados automaticamente com base nos flavors definidos
- O nome final do profile será `{name}-{vcpus}-{memory_gb}-{storage_size}` (ex: `infra-unified-1-1-20`)
- Certifique-se de que o storage pool especificado existe ou está sendo criado

### 2. Importar recursos existentes (se necessário)

Se você já possui bridges ou storage pools criados manualmente, pode importá-los:

```zsh
# Importar uplink network existente
terraform import incus_network.uplink[\"lxdbr0\"] lxdbr0

# Importar storage pool existente  
terraform import incus_storage_pool.this[\"local\"] local
```

### 3. Inicialize e valide o Terraform

```zsh
terraform init
terraform plan
```

### 4. Aplique o deploy

```zsh
terraform apply
```

Confirme a aplicação quando solicitado.

### 5. Verifique os recursos criados

- **Storage Pools:**
  ```zsh
  incus storage list
  incus storage show <nome-do-pool>
  ```

- **Uplink Networks:**
  ```zsh
  incus network show lxdbr0
  # Verifique se as rotas estão corretas em config.ipv4.routes
  ```

- **Profiles:**
  ```zsh
  incus profile list --project <projeto>
  incus profile show <nome-do-profile> --project <projeto>
  ```

- **Networks:**
  ```zsh
  incus network list --project <projeto>
  incus network show <nome-da-network> --project <projeto>
  ```

- **Projects:**
  ```zsh
  incus project list
  incus project show <nome-do-projeto>
  ```

## Arquitetura de Rede Unificada

Este módulo implementa uma arquitetura de rede unificada que consolidou as redes `infra-core` e `infra-apps` em uma única rede `infra-unified`. Benefícios:

- **Simplicidade**: Uma única rede para todos os serviços de infraestrutura
- **Conectividade**: Comunicação direta entre todos os serviços sem routing complexo
- **Load Balancers**: IPs dos load balancers no mesmo range da rede (10.191.1.100+)
- **Escalabilidade**: Range DHCP estendido (10.191.1.2-10.191.1.199) para comportar mais serviços

## Troubleshooting

### Erro: "Storage pool not found"
- Verifique se o storage pool especificado nos profiles existe
- Use `incus storage list` para ver pools disponíveis
- Considere usar "local" se for o pool padrão do seu sistema

### Erro: "Uplink network doesn't contain routes"
- Verifique se o uplink tem as rotas necessárias configuradas
- Use `incus network show lxdbr0` para verificar `config.ipv4.routes`
- As rotas devem incluir os IPs dos load balancers (ex: "10.191.1.100/32,10.191.1.101/32")

### Erro: "Profile doesn't exist" 
- Lembre-se que os profiles são criados com nomes compostos: `{name}-{vcpus}-{memory_gb}-{storage_size}`
- Ex: `infra-unified-1-1-20` para um flavor de 1 vCPU, 1GB RAM, 20GB storage

## Dicas

- **Storage Pools**: Use o pool "local" se já existir no sistema, ou crie novos conforme necessário
- **Uplinks**: O uplink das redes OVN deve ser uma bridge gerenciada pelo Incus (ex: lxdbr0)
- **Rotas**: Configure rotas no uplink para IPs de load balancers que ficam fora do range DHCP padrão
- **Projects**: Se usar projetos customizados, configure os uplinks permitidos conforme necessário
- **Profiles**: Use flavors para criar variações de recursos (CPU/memória/storage) do mesmo profile base
- **Import**: Para recursos existentes, use `terraform import` antes do primeiro apply

## Ordem de Deploy Recomendada

1. **000-incus** (este módulo) - infraestrutura base
2. **001-infra** - serviços DNS
3. **002-infra-services** - GLAuth e Vault
4. **003-vault** - configuração do Vault
5. **010-kubernetes-cluster** - cluster Kubernetes
6. Demais módulos conforme necessário

---

Documentação atualizada em junho de 2025 - GitHub Copilot.
