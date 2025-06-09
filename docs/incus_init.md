# Exemplo de configuração interativa do Incus (`incus admin init`)

Abaixo está um exemplo de execução do comando de configuração inicial do Incus em modo cluster, com explicação de cada etapa:

```shell
incus admin init
```

### Perguntas e respostas do assistente interativo

```
Would you like to use clustering? (yes/no) [default=no]: yes
```
> **Explicação:** Responda "yes" se deseja que este servidor faça parte de um cluster Incus (vários servidores trabalhando juntos). Caso contrário, responda "no" para uma instalação standalone.

```
What IP address or DNS name should be used to reach this server? [default=192.168.18.43]:
```
> **Explicação:** Informe o IP ou nome DNS pelo qual os outros membros do cluster poderão acessar este servidor. Se o valor padrão estiver correto, apenas pressione Enter.

```
Are you joining an existing cluster? (yes/no) [default=no]: no
```
> **Explicação:** Responda "yes" se este servidor vai se juntar a um cluster já existente. Se está criando um novo cluster, responda "no".

```
What member name should be used to identify this server in the cluster? [default=mgc]: nataliagranato
```
> **Explicação:** Defina um nome único para identificar este servidor dentro do cluster.

```
Do you want to configure a new local storage pool? (yes/no) [default=yes]: yes
```
> **Explicação:** Responda "yes" para criar um novo pool de armazenamento local para os containers e imagens.

```
Name of the storage backend to use (dir, lvm, btrfs) [default=btrfs]: btrfs
```
> **Explicação:** Escolha o tipo de backend de armazenamento. Recomenda-se `btrfs` para a maioria dos casos, pois oferece snapshots e clones rápidos.

```
Create a new BTRFS pool? (yes/no) [default=yes]: yes
```
> **Explicação:** Responda "yes" para criar um novo pool BTRFS.

```
Would you like to use an existing empty block device (e.g. a disk or partition)? (yes/no) [default=no]: no
```
> **Explicação:** Se você tem um disco ou partição vazio dedicado ao Incus, responda "yes" e informe o caminho. Caso contrário, responda "no" para usar um arquivo de imagem (loop device).

```
Size in GiB of the new loop device (1GiB minimum) [default=30GiB]: 30GiB
```
> **Explicação:** Defina o tamanho do pool de armazenamento. O valor padrão geralmente é suficiente para testes.

```
Do you want to configure a new remote storage pool? (yes/no) [default=no]: no
```
> **Explicação:** Responda "yes" se deseja configurar um pool de armazenamento remoto (ex: Ceph). Para a maioria dos casos, "no".

```
Would you like to use an existing bridge or host interface? (yes/no) [default=no]: no
```
> **Explicação:** Se não tem uma bridge de rede já configurada, responda "no" para o Incus criar uma bridge padrão automaticamente.

```
Would you like stale cached images to be updated automatically? (yes/no) [default=yes]: yes
```
> **Explicação:** Responda "yes" para que o Incus atualize automaticamente as imagens em cache.

```
Would you like a YAML "init" preseed to be printed? (yes/no) [default=no]: yes
```
> **Explicação:** Responda "yes" se deseja ver a configuração gerada em formato YAML (útil para automação ou reuso).

---

### Exemplo de preseed YAML gerado

```yaml
config:
  core.https_address: 192.168.18.43:8443
networks: []
storage_pools:
  - config:
      size: 30GiB
    description: ""
    name: local
    driver: btrfs
storage_volumes: []
profiles:
  - config: {}
    description: ""
    devices:
      root:
        path: /
        pool: local
        type: disk
    name: default
    project: default
projects: []
certificates: []
cluster:
  server_name: nataliagranato
  enabled: true
  member_config: []
  cluster_address: ""
  cluster_certificate: ""
  server_address: ""
  cluster_token: ""
  cluster_certificate_path: ""
```

Cada etapa do assistente pode ser ajustada conforme sua necessidade e ambiente. O YAML gerado pode ser reutilizado para automação de instalações futuras.