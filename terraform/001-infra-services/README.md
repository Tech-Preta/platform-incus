# Infraestrutura de Serviços

Este diretório contém a configuração Terraform para implantar os serviços de infraestrutura, incluindo Vault e GLAuth (LDAP).

## Estrutura do Projeto

```
001-infra-services/
├── glauth.tf           # Configuração do servidor LDAP (GLAuth)
├── vault.tf            # Configuração do servidor Vault
├── provider.tf         # Configuração dos providers Terraform
├── vars-global.tf      # Variáveis globais
└── templates/          # Templates de configuração
    ├── glauth/         # Templates do GLAuth
    └── vault/          # Templates do Vault
```

## Serviços Implantados

### 1. Vault (HashiCorp Vault)
- **IP do Load Balancer:** 10.191.1.101
- **Porta:** 8200 (HTTPS)
- **URL de Acesso:** https://10.191.1.101:8200

### 2. GLAuth (LDAP)
- **IP do Load Balancer:** 10.191.1.100
- **Portas:**
  - LDAP: 3893
  - LDAPS: 3894

## Deploy da Infraestrutura

1. **Inicialização do Terraform**
   ```bash
   terraform init
   ```

2. **Aplicação da Configuração**
   ```bash
   terraform apply -auto-approve
   ```

3. **Destruição da Infraestrutura (se necessário)**
   ```bash
   terraform destroy -auto-approve
   ```

## Configuração Inicial do Vault

### 1. Acesso Inicial
1. Acesse a URL do Vault: https://10.191.1.101:8200
2. Aceite o certificado autoassinado no navegador

### 2. Inicialização (Initialize)
1. Na tela inicial, configure:
   - **Key shares:** 1
   - **Key threshold:** 1
2. Clique em "Initialize"
3. **GUARDE** as informações exibidas:
   - Initial Root Token
   - Unseal Key

### 3. Unseal do Vault
1. Na tela de "Unseal Vault":
   - Cole a Unseal Key recebida
   - Clique em "Unseal"

### 4. Login
1. Após o unseal, clique em "Login"
2. Cole o Initial Root Token
3. Clique em "Sign In"

## Acesso ao GLAuth (LDAP)

O GLAuth não possui interface web nativa. Para acessar, use um cliente LDAP:

### Via Cliente LDAP
- **Host:** 10.191.1.100
- **Porta:** 3893 (LDAP) ou 3894 (LDAPS)
- **Base DN:** Conforme configurado no `glauth.tf`

### Clientes Recomendados
- Apache Directory Studio
- JXplorer
- ldapsearch (CLI)

## Segurança

### Certificados
- Todos os serviços usam certificados TLS autoassinados
- Para produção, considere usar certificados válidos

### Tokens e Chaves
- Guarde o Root Token e Unseal Key em local seguro
- Não compartilhe essas informações
- Considere usar um gerenciador de segredos para armazenar essas chaves

## Troubleshooting

### Vault
- Se o Vault estiver "sealed", use a Unseal Key para desbloqueá-lo
- Em caso de reinicialização, será necessário fazer unseal novamente

### GLAuth
- Verifique a conectividade usando `telnet` ou `nc`
- Teste a conexão LDAP com `ldapsearch`

## Próximos Passos

1. Configurar autenticação no Vault
2. Criar políticas de acesso
3. Configurar secrets engines
4. Implementar backup automático
5. Configurar monitoramento

## Notas Importantes

- Esta é uma configuração básica para desenvolvimento
- Para produção, considere:
  - Aumentar o número de key shares
  - Implementar backup automático
  - Configurar monitoramento
  - Usar certificados válidos
  - Implementar alta disponibilidade
