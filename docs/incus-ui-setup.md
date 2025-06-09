# Configuração de Certificados para Incus UI

## Arquivos Criados

### 1. Certificados
- ✅ `incus-ui.crt` - Certificado público (1805 bytes)
- ✅ `incus-ui.key` - Chave privada (3272 bytes) 
- ✅ `incus-ui.pfx` - Arquivo PKCS#12 para importar no browser (4211 bytes)

### 2. Token de Acesso (Nome: incus-ui)
```
eyJjbGllbnRfbmFtZSI6ImluY3VzLXVpIiwiZmluZ2VycHJpbnQiOiI8UkVNT1ZFRF9TRUNSRVQifQ==
```

## Comandos Executados

### 1. Limpeza dos certificados anteriores
```bash
# Remover certificado antigo do trust store
incus config trust remove 0ee84efac62a

# Remover arquivos antigos
rm -f incus-ui-cert.pem incus-ui-key.pem incus-ui-certificates.md
```

### 2. Criação dos novos certificados
```bash
# Criar certificado e chave no formato correto
openssl req -x509 -newkey rsa:4096 -keyout incus-ui.key -out incus-ui.crt -days 365 -nodes -subj "/CN=incus-ui"

# Criar arquivo .pfx para importar no browser (COM SENHA: 501917)
openssl pkcs12 -export -out incus-ui.pfx -inkey incus-ui.key -in incus-ui.crt -passout pass:501917

# Adicionar certificado ao Incus
incus config trust add incus-ui.crt

# Gerar token com nome específico
incus config trust add incus-ui
```

### 3. Verificação
```bash
incus config trust list
ls -la incus-ui.*
```

## Configuração no Browser

### Para Chrome/Chromium (Linux)
1. Faça o download do arquivo `incus-ui.pfx`
2. Abra o Chrome e digite na barra de endereços:
   ```
   chrome://settings/certificates
   ```
3. Clique no botão **Import** 
4. Selecione o arquivo `incus-ui.pfx`
5. Digite a senha: **501917**
6. Reinicie o browser
7. Acesse `https://192.168.18.43:8443`
8. Selecione o certificado **Incus-UI** quando solicitado

### Para Firefox
1. Faça o download do arquivo `incus-ui.pfx`
2. Vá em **Preferences** → **Privacy & Security** → **Certificates** → **View Certificates**
3. Na aba **Your Certificates**, clique em **Import**
4. Selecione o arquivo `incus-ui.pfx`
5. Digite a senha: **501917**
6. Reinicie o browser
7. Acesse `https://192.168.18.43:8443`

## Informações da Conexão

- **URL do Incus**: `https://192.168.18.43:8443`
- **Certificado**: `incus-ui.crt` (adicionado ao trust store do Incus)
- **Arquivo para browser**: `incus-ui.pfx` (senha: **501917**)
- **Validade**: 365 dias (até junho de 2026)

## Status Final

✅ Certificados criados corretamente no formato esperado pelo Incus UI
✅ Arquivo .pfx criado para importação no browser (senha: 501917)
✅ Certificado adicionado ao trust store do Incus
✅ Token de acesso gerado com nome 'incus-ui'

## Próximos Passos

1. Baixe o arquivo `incus-ui.pfx` para sua máquina local
2. Importe o certificado no seu browser seguindo as instruções acima
3. Acesse `https://192.168.18.43:8443` para usar a UI do Incus
4. Use o token gerado se necessário para autenticação adicional

