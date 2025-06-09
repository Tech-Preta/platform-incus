# 002-vault - Configuração do Vault com Autenticação LDAP

Este módulo configura o HashiCorp Vault com autenticação LDAP usando o GLAuth provisionado no módulo `001-infra-services`. O objetivo é estabelecer uma infraestrutura de segurança integrada com PKI, gerenciamento de segredos e autenticação centralizada.

## Pré-requisitos

1. **Módulo 001-infra-services implantado** com:
   - GLAuth LDAP Server executando em `10.191.1.100:3893/3894`
   - Vault Server executando em `10.191.1.101:8200`
   - Certificados TLS configurados

2. **Credenciais do Vault**:
   - Root token obtido durante a inicialização
   - Unseal key (se necessário)

## Estrutura do Módulo

```
002-vault/
├── provider.tf          # Configuração do provider Vault
├── variables.tf         # Definição de variáveis
├── terraform.tfvars     # Valores das variáveis
├── ldap.tf             # Configuração da autenticação LDAP
├── rbac.tf             # Políticas e mapeamento de grupos
├── mount.tf            # Secret engines KV
├── certs.tf            # PKI Infrastructure
└── common.tf           # Configurações comuns
```

## Configuração

### 1. Variables (terraform.tfvars)

```hcl
project = "infra-unified-1-1-20"

vault_config = {
  profile          = "infra-unified-1-1-20"
  common_name      = "vault-01"
  load_balancer_ip = "10.191.1.101"
}

ldap_config = {
  url          = "ldap://10.191.1.100:3893"
  binddn       = "cn=granato,dc=nataliagranato,dc=xyz"
  bindpass     = "123456"
  userdn       = "ou=admin,ou=users,dc=nataliagranato,dc=xyz"
  userattr     = "cn"
  groupdn      = "ou=groups,dc=nataliagranato,dc=xyz"
  groupattr    = "cn"
  insecure_tls = true
}

vault_token = "<REMOVED_SECRET>"
```

### 2. Provider Configuration

```hcl
provider "vault" {
  address         = "https://10.191.1.101:8200"
  skip_tls_verify = true
  token           = var.vault_token
}
```

## Estrutura LDAP e Permissões

### Estrutura do Diretório GLAuth

O GLAuth está configurado com a seguinte estrutura hierárquica:

```
dc=nataliagranato,dc=xyz
├── ou=users
│   ├── ou=admin
│   │   ├── cn=granato (uid: 10001, gid: 11001)
│   │   └── cn=vaultadmin (uid: 10002, gid: 11001)
│   └── ou=guest
└── ou=groups
    ├── ou=admin (gid: 11001)
    │   ├── uniqueMember: cn=granato,ou=admin,ou=users,dc=nataliagranato,dc=xyz
    │   └── uniqueMember: cn=vaultadmin,ou=admin,ou=users,dc=nataliagranato,dc=xyz
    └── ou=guest (gid: 11002)
```

### Configuração LDAP no Vault

#### Backend de Autenticação

```hcl
resource "vault_auth_backend" "ldap" {
  type        = "ldap"
  path        = "glauth-ldap"
  description = "LDAP authentication backend for GLAuth"
}

resource "vault_ldap_auth_backend" "ldap" {
  path            = "glauth-ldap"
  url             = "ldap://10.191.1.100:3893"
  binddn          = "cn=granato,dc=nataliagranato,dc=xyz"
  bindpass        = "123456"
  userdn          = "ou=admin,ou=users,dc=nataliagranato,dc=xyz"
  userattr        = "cn"
  groupdn         = "ou=groups,dc=nataliagranato,dc=xyz"
  groupattr       = "cn"
  insecure_tls    = true
  
  # Filtros específicos para GLAuth
  groupfilter = "(&(objectClass=groupOfUniqueNames)(uniqueMember=cn={{.Username}},ou=admin,ou=users,dc=nataliagranato,dc=xyz))"
  userfilter  = "(&(objectClass=posixAccount)(cn={{.Username}}))"
}
```

#### Problema de Dependências Circulares

**Problema Identificado**: O Terraform não está respeitando corretamente as dependências entre recursos, causando erros de aplicação quando recursos dependem uns dos outros de forma circular ou implícita.

**Manifestação do Problema**:
1. O `vault_ldap_auth_backend_group` tenta referenciar políticas antes delas serem criadas
2. Recursos PKI dependem de outros recursos PKI que ainda não foram provisionados
3. Secret engines são referenciados antes de serem montados

**Soluções Implementadas**:

1. **Dependências Explícitas**:
```hcl
resource "vault_ldap_auth_backend_group" "admin" {
  backend   = vault_auth_backend.ldap.path
  groupname = "admin"
  policies  = [vault_policy.admin.name]
  
  depends_on = [
    vault_ldap_auth_backend.ldap,
    vault_policy.admin
  ]
}
```

2. **Separação de Recursos em Arquivos Específicos**:
   - `ldap.tf`: Configuração base do LDAP
   - `rbac.tf`: Políticas e mapeamentos (dependem do LDAP)
   - `mount.tf`: Secret engines
   - `certs.tf`: PKI (depende de outros recursos)

3. **Ordem de Aplicação Recomendada**:
```bash
# Aplicar em etapas para evitar dependências circulares
terraform apply -target=vault_auth_backend.ldap
terraform apply -target=vault_ldap_auth_backend.ldap
terraform apply -target=vault_policy.admin
terraform apply -target=vault_policy.guest
terraform apply
```

### Políticas de Acesso (RBAC)

#### Política Admin
```hcl
resource "vault_policy" "admin" {
  name   = "admin"
  policy = <<-EOT
path "/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}
  EOT
}
```

#### Política Guest
```hcl
resource "vault_policy" "guest" {
  name   = "guest"
  policy = <<-EOT
path "guest/data/*" {
  capabilities = ["read", "list"]
}
path "guest/metadata/*" {
  capabilities = ["read", "list"]
}
  EOT
}
```

#### Política Read Environment
```hcl
resource "vault_policy" "read_env" {
  name   = "read-env"
  policy = <<-EOT
path "core/*" {
  capabilities = ["list"]
}
path "core/data/environment" {
  capabilities = ["read", "list"]
}
path "core/metadata/environment" {
  capabilities = ["read", "list"]
}
  EOT
}
```

### Mapeamento de Grupos

```hcl
# Grupo admin -> política admin
resource "vault_ldap_auth_backend_group" "admin" {
  backend   = vault_auth_backend.ldap.path
  groupname = "admin"
  policies  = [vault_policy.admin.name]
}

# Grupo guest -> políticas guest + read_env
resource "vault_ldap_auth_backend_group" "guest" {
  backend   = vault_auth_backend.ldap.path
  groupname = "guest"
  policies  = [vault_policy.guest.name, vault_policy.read_env.name]
}
```

## Secret Engines

### 1. KV Secret Engine - Core
```hcl
resource "vault_mount" "core" {
  type = "kv-v2"
  path = "core"
}
```

**Uso**: Armazenamento de configurações críticas e variáveis de ambiente.

### 2. KV Secret Engine - Guest
```hcl
resource "vault_mount" "guest" {
  type = "kv-v2"
  path = "guest"
}
```

**Uso**: Armazenamento de dados não-sensíveis acessíveis por usuários guest.

### 3. Secret Environment
```hcl
resource "vault_kv_secret_v2" "environment" {
  mount = vault_mount.core.path
  name  = "environment"
  
  data_json = jsonencode({
    VAULT_ADDR = "https://10.191.1.101:8200"
    LDAP_URL   = "ldap://10.191.1.100:3893"
  })
}
```

## PKI Infrastructure

### 1. PKI Root CA
```hcl
resource "vault_mount" "pki" {
  path                      = "pki"
  type                      = "pki"
  default_lease_ttl_seconds = 8640000  # 100 dias
  max_lease_ttl_seconds     = 8640000
}

resource "vault_pki_secret_backend_root_cert" "this" {
  backend     = vault_mount.pki.path
  type        = "internal"
  common_name = "Tech Preta Vault Root CA"
  ttl         = "86400"  # 24 horas
}
```

### 2. PKI Intermediate CA
```hcl
resource "vault_mount" "pki_intermediate" {
  path = "pki-intermediate"
  type = "pki"
}

resource "vault_pki_secret_backend_intermediate_cert_request" "intermediate" {
  backend     = vault_mount.pki_intermediate.path
  type        = "internal"
  common_name = "Tech Preta Vault Intermediate CA"
}
```

### 3. PKI Role
```hcl
resource "vault_pki_secret_backend_role" "this" {
  backend          = vault_mount.pki_intermediate.path
  name             = "pki"
  ttl              = "86400"
  max_ttl          = "86400"
  allow_ip_sans    = true
  key_bits         = 4096
  key_type         = "rsa"
  allowed_domains  = ["nataliagranato.xyz"]
  allow_subdomains = true
}
```

## Auditoria

```hcl
resource "vault_audit" "this" {
  type = "file"
  options = {
    file_path = "/opt/vault/audit.log"
  }
}
```

**Localização dos logs**: `/opt/vault/audit.log` no servidor Vault.

## Testes e Validação

### 1. Teste de Conectividade LDAP

```bash
# Testar conexão LDAP direta
ldapsearch -x -H ldap://10.191.1.100:3893 \
  -D "cn=granato,dc=nataliagranato,dc=xyz" \
  -w 123456 \
  -b "dc=nataliagranato,dc=xyz" \
  "(objectClass=*)"
```

**Resultado Esperado**: Listagem completa do diretório LDAP com usuários e grupos.

### 2. Teste de Autenticação Vault

```bash
# Limpar token existente
unset VAULT_TOKEN

# Fazer login via LDAP
VAULT_ADDR=https://10.191.1.101:8200 \
VAULT_SKIP_VERIFY=true \
vault login -method=ldap -path=glauth-ldap \
  username=granato password=123456
```

**Resultado Esperado**:
```
Success! You are now authenticated. The token information displayed below
is already stored in the token helper.

Key                    Value
---                    -----
token                  hvs.XXXXXXX...
token_accessor         <REMOVED_SECRET>
token_duration         768h
token_renewable        true
token_policies         ["default"]
identity_policies      ["admin"]
policies               ["admin" "default"]
token_meta_username    granato
```

### 3. Teste de Permissões Admin

```bash
# Verificar informações do token
VAULT_ADDR=https://10.191.1.101:8200 \
VAULT_SKIP_VERIFY=true \
vault token lookup

# Listar secret engines (requer permissão admin)
VAULT_ADDR=https://10.191.1.101:8200 \
VAULT_SKIP_VERIFY=true \
vault secrets list

# Acessar secret environment
VAULT_ADDR=https://10.191.1.101:8200 \
VAULT_SKIP_VERIFY=true \
vault kv get core/environment
```

### 4. Teste PKI

```bash
# Listar issuers PKI
VAULT_ADDR=https://10.191.1.101:8200 \
VAULT_SKIP_VERIFY=true \
vault list pki/issuers

# Verificar configuração do role
VAULT_ADDR=https://10.191.1.101:8200 \
VAULT_SKIP_VERIFY=true \
vault read pki-intermediate/roles/pki
```

### 5. Verificação da Configuração LDAP

```bash
# Verificar configuração do backend LDAP
VAULT_ADDR=https://10.191.1.101:8200 \
VAULT_SKIP_VERIFY=true \
VAULT_TOKEN=<REMOVED_SECRET> \
vault read auth/glauth-ldap/config

# Verificar grupos mapeados
VAULT_ADDR=https://10.191.1.101:8200 \
VAULT_SKIP_VERIFY=true \
VAULT_TOKEN=<REMOVED_SECRET> \
vault read auth/glauth-ldap/groups/admin
```

## Problemas Conhecidos e Soluções

### 1. GroupFilter Configuration

**Problema**: O filtro inicial `(&(objectClass=posixGroup)(memberUid={{.Username}}))` não funcionava porque o GLAuth usa `groupOfUniqueNames` com `uniqueMember`.

**Solução**: Atualizado para:
```
(&(objectClass=groupOfUniqueNames)(uniqueMember=cn={{.Username}},ou=admin,ou=users,dc=nataliagranato,dc=xyz))
```

### 2. PKI Intermediate Key Management

**Problema**: As chaves privadas do PKI intermediate não estão sendo mantidas após a assinatura, causando avisos sobre `key_id` ausente.

**Status**: Funcional para geração de certificados, mas requer revisão da configuração para produção.

### 3. Dependências Circulares do Terraform

**Problema**: Recursos interdependentes causam falhas durante `terraform apply`.

**Solução**: Aplicação em etapas ou uso de `depends_on` explícito.

## Próximos Passos

1. **Configurar usuários guest** no GLAuth para testar permissões limitadas
2. **Resolver configuração PKI** para manter chaves privadas corretamente
3. **Implementar rotação automática** de certificados
4. **Configurar backup** dos dados do Vault
5. **Implementar monitoramento** e alertas

## Estrutura de Arquivos Detalhada

```
002-vault/
├── provider.tf              # Provider Vault e versões
├── variables.tf             # Definições de variáveis
├── terraform.tfvars         # Valores das variáveis (contém secrets)
├── common.tf               # Configurações comuns (módulo common)
├── ldap.tf                 # Backend LDAP e configuração
├── rbac.tf                 # Políticas e mapeamento de grupos
├── mount.tf                # Secret engines KV e secrets
├── certs.tf                # Infraestrutura PKI completa
├── terraform.tfstate       # Estado atual do Terraform
└── README.md              # Esta documentação
```

## Comandos de Manutenção

### Deploy Completo
```bash
cd /home/nataliagranato/Downloads/platform-locals/terraform/002-vault
terraform init
terraform plan
terraform apply
```

### Deploy Incremental (evitar dependências circulares)
```bash
terraform apply -target=vault_auth_backend.ldap
terraform apply -target=vault_ldap_auth_backend.ldap
terraform apply -target=vault_policy.admin
terraform apply -target=vault_policy.guest
terraform apply -target=vault_policy.read_env
terraform apply
```

### Verificação do Estado
```bash
terraform show
terraform state list
```

### Limpeza (CUIDADO!)
```bash
terraform destroy  # Remove toda a configuração do Vault
```

---

**Autor**: Sistema automatizado de configuração  
**Data**: 9 de junho de 2025  
**Versão**: 1.0  
**Status**: ✅ Funcional com autenticação LDAP integrada