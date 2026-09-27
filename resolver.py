import re
import sqlite3
from pathlib import Path

from normalizar import norma_canonica

DB = Path(__file__).parent / "data" / "desafio1_bracis.db"


def carregar_leis() -> dict[tuple[str, int], int]:
    leis = {}

    con = sqlite3.connect(DB)

    for doc_id, texto in con.execute("SELECT id, texto FROM documentos WHERE natureza = 'dispositivo'"):
        m = re.match(r"Artigo\s+(\d+)\S*\s+d[oa]\s+(.{0,60})", texto)

        artigo, norma = int(m.group(1)), m.group(2) # type: ignore
        leis[(norma_canonica(norma), artigo)] = doc_id

    con.close()

    return leis

if __name__ == "__main__":
    for chave, doc_id in sorted(carregar_leis().items()):
        print(chave, doc_id)