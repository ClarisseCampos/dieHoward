#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [ ! -d ".venv" ]; then
    echo "❌ Ambiente virtual (.venv) não encontrado."
    echo "👉 Execute primeiro: ./install.sh"
    exit 1
fi

source .venv/bin/activate
export PYTHONPATH="$PROJECT_DIR"
exec python "$PROJECT_DIR/app/app.py" "$@"
