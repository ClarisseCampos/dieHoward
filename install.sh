#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "🎙️ Instalando DieHoward Audiobook Pipeline..."
echo "📂 Diretório do projeto: $PROJECT_DIR"

# 1. Verifica Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale-o antes de continuar."
    exit 1
fi

# 2. Cria ambiente virtual e instala dependências
if [ ! -d ".venv" ]; then
    echo "📦 Criando ambiente virtual (.venv)..."
    python3 -m venv .venv
fi

echo "⬇️ Instalando dependências do requirements.txt..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Garante estrutura de pastas locais (ignoradas pelo Git)
mkdir -p data/input data/output data/temp models/kokoro models/piper

# 4. Permissões de execução
chmod +x "$PROJECT_DIR/diehoward.sh"

# 5. Detecta automaticamente o logotipo dentro da pasta icons/
ICON_PATH=$(find "$PROJECT_DIR/icons" -maxdepth 1 -type f \( -iname "*.png" -o -iname "*.svg" -o -iname "*.jpg" -o -iname "*.webp" -o -iname "*.ico" \) | head -n 1)

if [ -n "$ICON_PATH" ]; then
    echo "🎨 Logotipo encontrado: $ICON_PATH"
else
    ICON_PATH="utilities-terminal"
    echo "⚠️ Nenhum ícone encontrado em icons/. Usando ícone padrão do terminal."
fi

# 6. Cria o atalho no Menu de Aplicativos com o caminho dinâmico do usuário
DESKTOP_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="$DESKTOP_DIR/diehoward.desktop"
mkdir -p "$DESKTOP_DIR"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Name=DieHoward TTS
Comment=Gerador de Audiobooks Local e Otimizado
Exec="$PROJECT_DIR/diehoward.sh"
Path=$PROJECT_DIR
Icon=$ICON_PATH
Terminal=true
Type=Application
Categories=AudioVideo;Audio;Education;
EOF

chmod +x "$DESKTOP_FILE"

# 7. Atualiza o cache de menus do desktop (Linux Mint / Cinnamon / XDG)
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

echo ""
echo "✔ Instalação concluída!"
echo "🚀 Você já pode abrir o 'DieHoward TTS' pelo menu de aplicativos ou rodar ./diehoward.sh"