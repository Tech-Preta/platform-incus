#!/bin/bash

# Configuração do Vault
export VAULT_ADDR="https://10.191.1.101:8200"
export VAULT_SKIP_VERIFY=true

# Configuração do LDAP
export LDAP_URL="ldap://10.191.1.100:3893"
export LDAP_BIND_DN="cn=granato,dc=nataliagranato,dc=xyz"
export LDAP_BIND_PASSWORD="123456"
export LDAP_BASE_DN="dc=nataliagranato,dc=xyz"

# Configuração do ambiente
export VAULT_ENV="infra-unified-1-1-20"

# Configuração do Terraform
# export TF_VAR_vault_token="<REMOVED_SECRET>"
