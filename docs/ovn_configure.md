# Instalação OVN e Configuração de Rede

1. Instalação dos Pacotes OVN

```bash
sudo apt update
sudo apt install ovn-host ovn-central openvswitch-switch
```
2. Configuração do Open vSwitch para OVN

```bash
sudo ovs-vsctl set open_vswitch . \
   external_ids:ovn-remote=unix:/run/ovn/ovnsb_db.sock \
   external_ids:ovn-encap-type=geneve \
   external_ids:ovn-encap-ip=127.0.0.1
```

3. Habilitação e Inicialização dos Serviços

# Habilitar serviços para iniciar automaticamente
```bash
sudo systemctl enable ovn-central ovn-host
```
# Iniciar os serviços
```bash
sudo systemctl start ovn-central ovn-host
```

# Verificar status
```bash
sudo systemctl status ovn-central ovn-host
```

4. Configuração da Rede Bridge no Incus

# Criar bridge principal (uplink)
```bash
incus network create lxcbr0 --type=bridge \
  ipv4.address=10.0.0.1/24 \
  ipv4.nat=true \
  ipv6.address=none
```
# Configurar ranges de IP
```bash
incus network set lxcbr0 \
  ipv4.dhcp.ranges=10.0.0.100-10.0.0.150 \
  ipv4.ovn.ranges=10.0.0.151-10.0.0.200
```

5. Criação da Rede OVN
```bash
# Criar rede OVN usando a bridge como uplink
incus network create ovn1 --type=ovn network=lxcbr0
```

6. Verificação da Configuração
```bash
# Verificar redes criadas
incus network list

# Verificar detalhes da rede OVN
incus network show ovn1

# Verificar serviços OVN
systemctl status ovn-northd ovn-ovsdb-server-nb ovn-ovsdb-server-sb ovn-controller
```

7. Teste com Container/VM

# Adicionar remote do Ubuntu (se necessário)
```bash
incus remote add ubuntu https://cloud-images.ubuntu.com/releases --protocol simplestreams
```
# Criar container usando a rede OVN

```bash
incus launch images:ubuntu/22.04 container1 --network ovn1
```

# Criar VM usando a rede OVN

```bash
incus launch images:ubuntu/22.04 vm1 --vm --network ovn1
```

# Verificar instâncias

```
incus list
```