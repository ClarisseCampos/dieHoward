#!/usr/bin/env bash
set -e

# Resolve o diretório real do script, mesmo se chamado via symlink
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [ ! -d ".venv" ]; then
    echo "❌ Ambiente virtual (.venv) não encontrado."
    echo "👉 Execute './install.sh' primeiro para configurar o DieHoward."
    read -rp "Pressione Enter para sair..."
    exit 1
fi

source .venv/bin/activate
exec python app.py "$@"