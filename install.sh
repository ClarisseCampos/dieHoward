#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "🎙️ Instalando DieHoward Audiobook Pipeline..."
echo "📂 Diretório do projeto: $PROJECT_DIR"

# 1. Detecta Python 3.10 ou superior
PYTHON_BIN=""
for cmd in python3.12 python3.11 python3.10 python3; do
    if command -v "$cmd" &> /dev/null; then
        if "$cmd" -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
            PYTHON_BIN="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "❌ Python 3.10 ou superior não encontrado."
    echo "👉 Ubuntu/Mint: sudo apt update && sudo apt install -y python3 python3-venv"
    echo "👉 Rocky/Fedora/RHEL: sudo dnf install -y python3.11"
    exit 1
fi

echo "🐍 Usando interpretador: $PYTHON_BIN ($($PYTHON_BIN --version))"

# 2. Verifica biblioteca de sistema libsndfile (necessária para o soundfile)
if command -v ldconfig &> /dev/null && ! ldconfig -p | grep -q libsndfile; then
    echo "⚠️ Biblioteca 'libsndfile' não detectada no sistema."
    echo "   Se ocorrer erro ao gerar áudio, instale com:"
    echo "   • Ubuntu/Mint: sudo apt install -y libsndfile1"
    echo "   • Rocky/Fedora: sudo dnf install -y libsndfile"
fi

# 3. Cria ambiente virtual e instala dependências
if [ ! -d ".venv" ]; then
    echo "📦 Criando ambiente virtual (.venv)..."
    "$PYTHON_BIN" -m venv .venv
fi

echo "⬇️ Instalando dependências do requirements.txt..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r app/requirements.txt

# 4. Garante estrutura de pastas locais e baixa os modelos TTS se ausentes
mkdir -p data/input data/output data/temp models/kokoro models/piper
python -c "from common.model_downloader import ModelDownloader; ModelDownloader.garantir_modelos()"

# 5. Permissões de execução
chmod +x "$PROJECT_DIR/diehoward.sh"

# 6. Detecta automaticamente o logotipo dentro da pasta icons/
ICON_PATH=$(find "$PROJECT_DIR/icons" -maxdepth 1 -type f \( -iname "*.png" -o -iname "*.svg" -o -iname "*.jpg" -o -iname "*.webp" -o -iname "*.ico" \) 2>/dev/null | head -n 1)

if [ -n "$ICON_PATH" ]; then
    echo "🎨 Logotipo encontrado: $ICON_PATH"
else
    ICON_PATH="utilities-terminal"
fi

# 7. Cria o atalho no Menu de Aplicativos
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

if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

echo ""
echo "✔ Instalação concluída!"
echo "🚀 Abra 'DieHoward TTS' pelo menu de aplicativos ou execute: ./diehoward.sh"