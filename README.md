# Plataform Locals

## Atualização automática do DNS do host

O script `update-resolved-dns.sh` atualiza automaticamente o arquivo `/etc/systemd/resolved.conf` do host com o IP do servidor DNS provisionado pelo Terraform. Após atualizar o arquivo, o script reinicia o serviço `systemd-resolved` para aplicar as mudanças.

### Como usar

1. Certifique-se de que o Terraform já aplicou a infraestrutura e que o output `dns_ips` está disponível.
2. Execute o script a partir do diretório raiz do projeto:

   ```bash
   bash update-resolved-dns.sh
   ```

3. O script irá solicitar sua senha de sudo para atualizar o arquivo de configuração e reiniciar o serviço.

## Requisito: systemd-resolved

É necessário que o serviço `systemd-resolved` esteja instalado e habilitado tanto na máquina host quanto nos containers DNS provisionados.

### Instalação no host (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install systemd systemd-resolved
sudo systemctl enable systemd-resolved
sudo systemctl start systemd-resolved
```

### Instalação nos containers (via cloud-init)

O cloud-init dos containers DNS já inclui a instalação do `systemd-resolved` e a configuração adequada para garantir que o serviço esteja disponível e funcional.

Se for necessário instalar manualmente em outros containers, utilize:

```bash
sudo apt update
sudo apt install systemd systemd-resolved
sudo systemctl enable systemd-resolved
sudo systemctl start systemd-resolved
```

## Observações
- Sempre verifique se o serviço está ativo com:
  ```bash
  systemctl status systemd-resolved
  ```
- O script faz backup do arquivo original `/etc/systemd/resolved.conf` antes de qualquer alteração.