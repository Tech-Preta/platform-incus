# Terraform Secure Template

Este repositório é um template para projetos Terraform, com foco em segurança desde o início. Ele integra práticas, ferramentas e automações para garantir a proteção do código, infraestrutura e cadeia de dependências.

## Funcionalidades

- **Pipeline CI/CD seguro** com validações automáticas
- **Análise de segurança de código e dependências**
- **Política de permissões mínimas no GitHub Actions**
- **Pronto para uso em novos projetos Terraform**

## Workflows e Soluções de Segurança

### 1. Terraform Format, Validate, and Test
- **Arquivo:** `.github/workflows/terraform.yml`
- **Função:** Formata, valida e executa testes em código Terraform a cada push ou pull request.
- **Segurança:** Utiliza o bloco `permissions` para garantir acesso mínimo (`contents: read`).

### 2. Checkov Security Scan
- **Arquivo:** `.github/workflows/checkov.yml`
- **Função:** Executa o [Checkov](https://www.checkov.io/) para análise estática de segurança em código IaC (Infrastructure as Code), gerando relatórios SARIF.
- **Segurança:** Detecta más práticas, configurações inseguras e vulnerabilidades em arquivos Terraform.

### 3. Trivy SBOM & Vulnerability Scan
- **Arquivo:** `.github/workflows/trivy.yml`
- **Função:** Gera SBOM (Software Bill of Materials) e faz varredura de vulnerabilidades em dependências e imagens, integrando resultados ao GitHub Dependency Graph.
- **Segurança:** Ajuda a identificar componentes vulneráveis presentes no projeto.

### 4. Scorecard Supply-chain Security
- **Arquivo:** `.github/workflows/scorecard.yml`
- **Função:** Usa o [OSSF Scorecard](https://github.com/ossf/scorecard) para avaliar práticas de segurança da cadeia de suprimentos do repositório.
- **Segurança:** Analisa branch protection, dependabot, workflows, tokens, entre outros.

### 5. OSV-Scanner
- **Arquivo:** `.github/workflows/osv-scanner.yml`
- **Função:** Executa o [OSV-Scanner](https://osv.dev/) para identificar vulnerabilidades conhecidas em dependências.
- **Segurança:** Automatiza a checagem contínua de vulnerabilidades em bibliotecas e módulos.

### 6. Dependency Review
- **Arquivo:** `.github/workflows/dependency-review.yml`
- **Função:** Bloqueia PRs que introduzem dependências vulneráveis conhecidas, usando o GitHub Dependency Review Action.
- **Segurança:** Garante que novas dependências estejam livres de vulnerabilidades conhecidas.

### 7. CodeQL Analysis (opcional)
- **Arquivo:** (não incluído por padrão)
- **Função:** Executa análise estática de segurança aprofundada com CodeQL para identificar vulnerabilidades no código.
- **Segurança:** Detecta padrões de código problemáticos que podem levar a vulnerabilidades, com base em queries mantidas pela comunidade e pelo GitHub.
- **Observação:** O uso do CodeQL é recomendado e está documentado em [SECURITY.md](SECURITY.md), mas o workflow não está incluído por padrão neste template. Para habilitar, utilize a opção "Configure CodeQL" na aba "Security" do GitHub ou adicione manualmente o workflow sugerido pela plataforma.

## Outras Práticas de Segurança

- **Dependabot:** Atualizações automáticas de dependências.
- **Política de Segurança:** Veja [SECURITY.md](SECURITY.md) para detalhes sobre reporte de vulnerabilidades e práticas adotadas.
- **Code of Conduct:** Ambiente colaborativo e respeitoso ([CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)).

## Como usar este template

1. Clique em `Use this template` no GitHub.
2. Siga as instruções para criar seu novo repositório.
3. Adapte os workflows conforme as necessidades do seu projeto.

## Contato

Para dúvidas ou reporte de vulnerabilidades, consulte o [SECURITY.md](SECURITY.md).

---

Feito com ❤️ por [Natália Granato](https://github.com/nataliagranato).
