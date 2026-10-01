#!/usr/bin/env bash
# Uso: bash run.sh [pasta_txt] [saida.csv]
# Espera a base em data/desafio1_bracis.db. O pipeline só usa a biblioteca padrão (Python 3.10+).
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")" && pwd)"
TXT="$(realpath -m "${1:-$RAIZ/data/txt}")"
SAIDA="$(realpath -m "${2:-$RAIZ/out/submission.csv}")"

cd "$RAIZ"
python3 main.py "$TXT"

if [ "$SAIDA" != "$RAIZ/out/submission.csv" ]; then
    mkdir -p "$(dirname "$SAIDA")"
    cp out/submission.csv "$SAIDA"
fi
