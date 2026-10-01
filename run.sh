#!/usr/bin/env bash
# Uso: bash run.sh <caminho_db> <pasta_txt> <arquivo_saida>
# Só usa a biblioteca padrão (Python 3.10+). O índice é reconstruído do .db a cada execução.
set -euo pipefail

if [ $# -ne 3 ]; then
    echo "uso: bash run.sh <caminho_db> <pasta_txt> <arquivo_saida>" >&2
    exit 2
fi

RAIZ="$(cd "$(dirname "$0")" && pwd)"
DB="$(realpath -m "$1")"
TXT="$(realpath -m "$2")"
SAIDA="$(realpath -m "$3")"

mkdir -p "$(dirname "$SAIDA")"
cd "$RAIZ"
python3 main.py "$TXT" --db "$DB" --saida "$SAIDA"
