# Instalação do Incus no Debian

## Passo a Passo: Instalação do Incus no Debian

### 1. Atualizar o sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Instalar dependências necessárias
```bash
sudo apt install -y curl gnupg lsb-release```

### 3. Adicionar a chave GPG do repositório Zabbly
```bash
curl -fsSL https://pkgs.zabbly.com/key.asc | sudo gpg --dearmor -o /etc/apt/keyrings/zabbly.gpg```

### 4. Adicionar o repositório do Incus
```bash
echo "deb [signed-by=/etc/apt/keyrings/zabbly.gpg] https://pkgs.zabbly.com/incus/stable $(lsb_release -sc) main" | sudo tee /etc/apt/sources.list.d/zabbly-incus-stable.list
```

### 5. Atualizar a lista de pacotes
```bash
sudo apt update
```

### 6. Instalar o Incus
```bash
sudo apt install -y incus
```

### 7. Adicionar seu usuário ao grupo incus-admin
```bash
sudo usermod -aG incus-admin $USER
```

### 8. Habilitar e iniciar os serviços do Incus
```bash
sudo systemctl enable incus
sudo systemctl start incus```

### 9. Verificar se o daemon está rodando
```bash
systemctl status incus-daemon
```

### 10. Fazer logout e login novamente
Para que as mudanças de grupo tenham efeito, você precisa fazer logout e login novamente, ou executar:
```bash
newgrp incus-admin
```

### 11. Inicializar o Incus (configuração inicial)
```bash
incus admin init
```

### 12. Verificar a instalação
```bash
incus remote switch local
incus version
incus list```

Notas importantes:

•  Reinicialização de sessão: Após adicionar o usuário ao grupo incus-admin, é necessário fazer logout/login ou usar newgrp incus-admin
•  Configuração inicial: O comando incus admin init é interativo e permite configurar storage pools, redes, etc.
•  Dependências opcionais: Para funcionalidades avançadas, considere instalar zfsutils-linux para suporte a ZFS
•  Firewall: Se você usar firewall, pode precisar configurar regras para o Incus

Este é o procedimento padrão e mais seguro para instalar o Incus no Debian. Cada passo tem sua importância para garantir uma instalação correta e funcional.