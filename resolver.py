import re
import sqlite3
from pathlib import Path

from normalizar import classes_processuais, digitos_ocr, norma_canonica

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

RE_NUM_CABECALHO = re.compile(r"(?<![\d/])\d(?:[\d.\-]|[.\-] )*\d(?!\d)")
RE_CNJ_TST = r"\d{1,7}-\d{2}\.\d{4}\.5\.\d{2}\.\d{4}"


def numero_do_cabecalho(tribunal: str, texto: str) -> tuple[str, str] | None:
    if tribunal == "TST":
        m = (re.search(rf"discutidos\s+estes\s+autos.{{0,250}}?({RE_CNJ_TST})", texto, re.S)
            or re.search(rf"TST-[\sA-Za-z\-]*?({RE_CNJ_TST})", texto))
            
        return (m.group(1), texto[max(0, m.start(1) - 150):m.start(1)]) if m else None

    cabecalho = texto[:400]

    for m in RE_NUM_CABECALHO.finditer(cabecalho):
        if re.fullmatch(r"\d\d/\d\d/\d{4}", m.group(0)):
            continue # data da sessão
        
        if re.match(r"/\d", cabecalho[m.end():m.end() + 2]):
            continue # "2016/0115164-6"
        
        return m.group(0), cabecalho[max(0, m.start() - 120):m.start()]
    
    return None


def carregar_indice() -> dict[str, list[dict]]:
    indice = {}
    con = sqlite3.connect(DB)

    for doc_id, tribunal, texto in con.execute("SELECT id, tribunal, texto FROM documentos WHERE natureza = 'acordao'"):
   
        achado = numero_do_cabecalho(tribunal, texto)
        
        if achado is None:
            continue
        
        numero, antes = achado
        
        indice.setdefault(digitos_ocr(numero), []).append({
            "id": doc_id,
            "classes": classes_processuais(antes),
            "cabecalho": texto[:300],
        })
    
    con.close()
    
    return indice


def carregar_sumulas() -> dict[tuple[bool, int], tuple[int, str]]:
    sumulas = {}

    con = sqlite3.connect(DB)

    for doc_id, tribunal, texto in con.execute("SELECT id, tribunal, texto FROM documentos WHERE natureza = 'sumula'"):
        m = re.match(r"Súmula\s+(Vinculante\s+)?n\.\s*(\d+)", texto)
        
        assert m is not None
        sumulas[(bool(m.group(1)), int(m.group(2)))] = (doc_id, tribunal)
    
    con.close()
    
    return sumulas