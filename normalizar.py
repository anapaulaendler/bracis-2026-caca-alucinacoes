import re
import unicodedata

def sem_acento(s: str) -> str:
    s = unicodedata.normalize("NFKD", s) # https://unicode.org/reports/tr15/ (ver figura 6)

    letras = []
    for c in s:
        e_acento = unicodedata.combining(c)
        if not e_acento:
            letras.append(c)

    return "".join(letras).lower()

def so_digitos(s: str) -> str:
    return re.sub(r"\D", "", s)

LEI_POR_NUMERO = {
    "4737": "CE",
    "1001": "CPM",
    "10406": "CC",
    "13105": "CPC",
    "8078": "CDC",
    "5452": "CLT",
    "3689": "CPP",
}

LEI_POR_NOME = {
    "processo civil": "CPC",
    "processo penal": "CPP",
    "defesa do consumidor": "CDC",
    "leis do trabalho": "CLT",
    "penal militar": "CPM",
    "codigo civil": "CC",
    "codigo eleitoral": "CE",
    "constitui": "CF",
    "ce": "CE", "cc": "CC", "cpc": "CPC", "cpp": "CPP", "cpm": "CPM", "clt": "CLT", "cdc": "CDC", "cf": "CF",
}

def norma_canonica(nome: str) -> str:
    s = sem_acento(nome)

    if re.search(r"complementar\D{0,10}64\b", s):
        return "LC64"

    m = re.search(r"lei\D{0,10}?([\d.]+)", s)
    if m:
        numero = so_digitos(m.group(1))

        return LEI_POR_NUMERO.get(numero, f"LEI{numero}")

    for pedaco, sigla in LEI_POR_NOME.items():
        if re.search(rf"\b{pedaco}", s):
            return sigla

    return "?"

def chave_lei(trecho: str) -> tuple[str, int] | None:
    m = re.match(r"art\w*\.?\s*(\d[\d.]*)", trecho, re.IGNORECASE)

    if not m:
        return None
    
    artigo = int(so_digitos(m.group(1)))

    norma = re.split(r"\s+d[oa]\s+", trecho, maxsplit=1)[1]
    return (norma_canonica(norma), artigo)