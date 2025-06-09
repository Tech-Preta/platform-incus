# Guia de Destruição Completa do Projeto Platform Control

Este documento descreve o processo completo de destruição segura da infraestrutura Platform Control, incluindo limpeza de segredos, destruição de recursos Terraform e reset completo do ambiente Incus.

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Pré-requisitos](#pré-requisitos)
3. [Processo de Destruição](#processo-de-destruição)
4. [Limpeza de Segredos](#limpeza-de-segredos)
5. [Destruição Terraform](#destruição-terraform)
6. [Limpeza Manual Incus](#limpeza-manual-incus)
7. [Verificação Final](#verificação-final)
8. [Troubleshooting](#troubleshooting)

## 🎯 Visão Geral

A destruição completa do projeto Platform Control envolve múltiplas etapas para garantir:

- **Segurança**: Remoção de todos os segredos antes do commit
- **Integridade**: Destruição ordenada dos recursos Terraform
- **Limpeza**: Reset completo do ambiente Incus
- **Documentação**: Preservação do conhecimento para reconstrução

## ⚠️ Pré-requisitos

### Ferramentas Necessárias
```bash
# Verificar se as ferramentas estão instaladas
terraform --version
incus --version
git --version
```

### Backup de Dados Importantes
```bash
# Fazer backup do estado atual (opcional)
cp -r terraform/ backup-terraform-$(date +%Y%m%d-%H%M%S)/

# Backup das configurações Incus (opcional)
incus config show > incus-config-backup.yaml
```

## 🗂️ Processo de Destruição

### Ordem de Execução
O processo deve seguir a ordem específica para evitar dependências quebradas:

1. **Limpeza de Segredos** (Primeiro)
2. **Destruição Terraform** (Por ordem de dependência)
3. **Limpeza Manual Incus** (Último)

## 🔐 Limpeza de Segredos

### 1. Identificar Arquivos com Segredos
```bash
# Buscar por tokens Vault
grep -r "hvs\." terraform/ --exclude-dir=.terraform

# Buscar por senhas em hash
grep -r "\$2a\$" terraform/ --exclude-dir=.terraform

# Buscar por outros segredos conhecidos
grep -r -E "(password|secret|token|key)" terraform/ --exclude-dir=.terraform
```

### 2. Arquivos Comuns com Segredos
- `terraform/*/terraform.tfvars`
- `terraform/*/profile.sh`
- `terraform/*/README.md`
- `terraform/vault_secret.md`
- `docs/incus-ui-setup.md`

### 3. Substituir Segredos
```bash
# Exemplo de substituição segura
sed -i 's/hvs\.[a-zA-Z0-9_-]*/<REMOVED_SECRET>/g' arquivo.tf
sed -i 's/\$2a\$[a-zA-Z0-9\/.]*/<REMOVED_SECRET>/g' arquivo.tf
```

### 4. Verificar Limpeza
```bash
# Verificar se não há mais segredos
git diff --name-only
git add .
git commit --amend -m "Remove all secrets before destruction"
git push --force-with-lease
```

## 🏗️ Destruição Terraform

### 1. Ordem de Destruição por Módulo

#### Módulo 013 - Kubernetes Services
```bash
cd terraform/013-kubernetes-services
terraform destroy -auto-approve
```

#### Módulo 012 - Kubernetes Core
```bash
cd terraform/012-kubernetes-core
terraform destroy -auto-approve
```

#### Módulo 011 - Kubernetes CRDs
```bash
cd terraform/011-kubernetes-crds
terraform destroy -auto-approve
```

#### Módulo 010 - Kubernetes Cluster
```bash
cd terraform/010-kubernetes-cluster
terraform destroy -auto-approve
```

#### Módulo 002 - Vault
```bash
cd terraform/002-vault
terraform destroy -auto-approve
```

#### Módulo 001 - Infra Services
```bash
cd terraform/001-infra-services
terraform destroy -auto-approve
```

#### Módulo 000 - Incus Base
```bash
cd terraform/000-incus
terraform destroy -auto-approve
```

### 2. Verificar Estado Terraform
```bash
# Para cada módulo, verificar que não há recursos
terraform show
terraform state list
```

### 3. Problemas Comuns na Destruição

#### Erro: Recursos em Uso
```bash
# Se houver erro de "resource in use"
incus list --all-projects
incus image list --all-projects

# Remover instâncias manualmente se necessário
incus delete <instance-name> --force --project <project>
```

#### Erro: Network Dependencies
```bash
# Verificar uso das redes
incus network show <network-name>

# Editar perfis que usam a rede
incus profile edit default --project <project>
```

## 🧹 Limpeza Manual Incus

### 1. Verificar Estado Inicial
```bash
# Listar todos os projetos
incus project list

# Listar todas as redes
incus network list

# Listar instâncias em todos os projetos
incus list --all-projects
```

### 2. Limpeza de Projetos

#### Projeto Apps
```bash
# Verificar conteúdo
incus list --project apps
incus image list --project apps
incus storage volume list local --project apps

# Remover imagens
incus image delete <image-fingerprint> --project apps

# Limpar perfil default
# (Criar arquivo temporário com configuração limpa)
cat > /tmp/profile-clean.yaml << EOF
config: {}
description: Default Incus profile for project apps
devices: {}
name: default
EOF

# Deletar projeto
incus project delete apps
```

#### Projeto Infra
```bash
# Mesmo processo do projeto apps
incus list --project infra
incus image list --project infra
incus storage volume list local --project infra

# Remover imagens
incus image delete <image-fingerprint> --project infra

# Deletar projeto
incus project delete infra
```

### 3. Limpeza de Redes

```bash
# Verificar redes gerenciadas
incus network list | grep "YES.*CREATED"

# Remover redes em ordem de dependência
incus network delete infra-unified
incus network delete ovn1
incus network delete lxdbr0
```

### 4. Verificação Final
```bash
# Verificar que apenas o projeto default existe
incus project list

# Verificar que apenas redes do sistema existem
incus network list

# Verificar que não há instâncias
incus list --all-projects
```

## ✅ Verificação Final

### 1. Estado do Git
```bash
# Verificar que não há segredos
git log --oneline -5
git show HEAD

# Status limpo
git status
```

### 2. Estado Terraform
```bash
# Para cada módulo, verificar estado vazio
for dir in terraform/0*; do
    echo "=== $dir ==="
    cd "$dir"
    terraform show
    cd - > /dev/null
done
```

### 3. Estado Incus
```bash
# Apenas projeto default deve existir
incus project list

# Apenas redes do sistema devem existir
incus network list | grep -v "docker\|br-\|ovs\|lo\|enp\|wlp\|lxcbr0"
```

## 🔧 Troubleshooting

### Problema: Terraform State Lock
```bash
# Se houver lock do estado
terraform force-unlock <lock-id>
```

### Problema: Rede "In Use"
```bash
# Identificar o que usa a rede
incus network show <network-name>

# Verificar perfis
incus profile list --all-projects
incus profile show default --project <project>

# Editar perfil para remover dispositivo de rede
incus profile edit default --project <project>
```

### Problema: Projeto Não Remove
```bash
# Verificar conteúdo do projeto
incus storage volume list local --project <project>
incus image list --project <project>
incus profile list --project <project>

# Limpar todos os recursos antes de deletar
```

### Problema: Instância Não Remove
```bash
# Forçar parada e remoção
incus stop <instance> --force --project <project>
incus delete <instance> --force --project <project>
```

## 📊 Resultado Esperado

Após completar todos os passos:

### ✅ Git Repository
- ✅ Nenhum segredo exposto
- ✅ Histórico limpo com force push
- ✅ Documentação atualizada

### ✅ Terraform
- ✅ Todos os módulos com `terraform show` vazio
- ✅ Nenhum recurso gerenciado
- ✅ States limpos

### ✅ Incus
- ✅ Apenas projeto `default`
- ✅ Nenhuma instância ativa
- ✅ Apenas redes do sistema (Docker, OVS, interfaces físicas)
- ✅ Nenhuma rede gerenciada pela plataforma

## 📝 Logs de Exemplo

### Destruição Bem-sucedida
```
❯ terraform destroy -auto-approve
incus_project.this["infra"]: Refreshing state... [name=infra]
incus_project.this["apps"]: Refreshing state... [name=apps]
incus_network.uplink["lxdbr0"]: Refreshing state... [name=lxdbr0]

No changes. No objects need to be destroyed.

Either you have not created any objects yet or the existing
objects were already deleted outside of Terraform.

Destroy complete! Resources: 0 destroyed.
```

### Limpeza Incus Concluída
```
❯ incus project list
+-------------------+--------+----------+-----------------+-----------------+--------+---------------+-----------------------+---------+
|       NAME        | IMAGES | PROFILES | STORAGE VOLUMES | STORAGE BUCKETS | NETWORKS | NETWORK ZONES |      DESCRIPTION      | USED BY |
+-------------------+--------+----------+-----------------+-----------------+--------+---------------+-----------------------+---------+
| default (current) | YES    | YES      | YES             | YES             | YES    | YES           | Default Incus project | 5       |
+-------------------+--------+----------+-----------------+-----------------+--------+---------------+-----------------------+---------+
```

## 🚀 Próximos Passos

Após a destruição completa:

1. **Reconstrução**: Use o README.md principal para reconstruir a plataforma
2. **Desenvolvimento**: Ambiente limpo para novas funcionalidades
3. **Aprendizado**: Documentação completa como referência
4. **Backup**: Considere manter backups das configurações importantes

---

**⚠️ AVISO**: Este processo é irreversível. Certifique-se de ter backups de dados importantes antes de prosseguir.