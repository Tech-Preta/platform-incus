#!/bin/bash

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para verificar se um comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Função para imprimir mensagens
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
    print_error "Por favor, execute este script como root (sudo)"
    exit 1
fi

# Atualizar repositórios
print_message "Atualizando repositórios..."
apt update

# Instalar Vault CLI
print_message "Instalando Vault CLI..."
if ! command_exists vault; then
    # Adicionar repositório HashiCorp
    wget -q -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list > /dev/null
    apt update
    apt install -y vault
else
    print_warning "Vault CLI já está instalado"
fi

# Instalar ferramentas LDAP
print_message "Instalando ferramentas LDAP..."
apt install -y ldap-utils

# Instalar Java
print_message "Instalando Java (JRE)..."
apt install -y default-jre

# Verificar instalação do Java
if ! command_exists java; then
    print_error "Falha ao instalar Java. Abortando instalação do Apache Directory Studio."
    exit 1
fi

# Instalar Apache Directory Studio
print_message "Instalando Apache Directory Studio..."
if [ ! -d "/opt/ApacheDirectoryStudio" ]; then
    # Criar diretório temporário
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"

    # Download do Apache Directory Studio
    print_message "Baixando Apache Directory Studio..."
    wget -q https://dlcdn.apache.org/directory/studio/2.0.0.v20210717-M17/ApacheDirectoryStudio-2.0.0.v20210717-M17-linux.gtk.x86_64.tar.gz

    # Descompactar
    print_message "Descompactando..."
    tar xzf ApacheDirectoryStudio-2.0.0.v20210717-M17-linux.gtk.x86_64.tar.gz

    # Mover para /opt
    print_message "Instalando em /opt..."
    mv ApacheDirectoryStudio /opt/

    # Criar link simbólico
    ln -sf /opt/ApacheDirectoryStudio/ApacheDirectoryStudio /usr/local/bin/apache-directory-studio

    # Criar arquivo .desktop
    cat > /usr/share/applications/apache-directory-studio.desktop << EOF
[Desktop Entry]
Name=Apache Directory Studio
Comment=LDAP Browser and Directory Client
Exec=/opt/ApacheDirectoryStudio/ApacheDirectoryStudio
Icon=/opt/ApacheDirectoryStudio/icon.xpm
Terminal=false
Type=Application
Categories=Development;
EOF

    # Limpar
    cd - > /dev/null
    rm -rf "$TEMP_DIR"

    print_message "Apache Directory Studio instalado com sucesso!"
else
    print_warning "Apache Directory Studio já está instalado"
fi

# Criar arquivo de configuração do Vault
print_message "Criando arquivo de configuração do Vault..."
cat > ~/.vault_config << EOF
export VAULT_ADDR='https://10.191.1.101:8200'
export VAULT_SKIP_VERIFY=true
EOF

# Adicionar configuração ao .bashrc
if ! grep -q "VAULT_ADDR" ~/.bashrc; then
    echo "source ~/.vault_config" >> ~/.bashrc
fi

# Criar arquivo de exemplo para ldapsearch
print_message "Criando arquivo de exemplo para ldapsearch..."
cat > ~/ldap-examples.txt << EOF
# Exemplos de uso do ldapsearch:

# Listar todos os usuários
ldapsearch -H ldap://10.191.1.100:3893 -x -b "dc=example,dc=com" "(objectClass=person)"

# Buscar um usuário específico
ldapsearch -H ldap://10.191.1.100:3893 -x -b "dc=example,dc=com" "(cn=usuario1)"

# Listar todos os grupos
ldapsearch -H ldap://10.191.1.100:3893 -x -b "dc=example,dc=com" "(objectClass=groupOfNames)"
EOF

print_message "Instalação concluída!"
print_message "Para usar o Vault CLI, execute: source ~/.vault_config"
print_message "Exemplos de uso do ldapsearch estão em: ~/ldap-examples.txt"
print_message "Apache Directory Studio pode ser iniciado pelo menu de aplicativos ou executando 'apache-directory-studio'"

# Instruções finais
echo -e "\n${GREEN}Próximos passos:${NC}"
echo "1. Execute 'source ~/.vault_config' para configurar o Vault CLI"
echo "2. Abra o Apache Directory Studio pelo menu de aplicativos ou execute 'apache-directory-studio'"
echo "3. Configure uma nova conexão LDAP com:"
echo "   - Hostname: 10.191.1.100"
echo "   - Port: 3893 (LDAP) ou 3894 (LDAPS)"
echo "   - Base DN: conforme configurado no glauth.tf"
echo "4. Consulte ~/ldap-examples.txt para exemplos de comandos ldapsearch" 