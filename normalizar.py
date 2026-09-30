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

OCR = {"O": "0", "o": "0", "l": "1", "I": "1", "S": "5", "s": "5", "g": "9", "G": "6", "B": "8"}
LETRAS_OCR = "".join(OCR)
OCR_PARA_DIGITO = str.maketrans(OCR) # tabelinha para tradução

# (?-i:) pq os regex de artigo usam IGNORECASE (e b/i minúsculos não estão em OCR)
NUM_ARTIGO = (
    rf"(?:\d|(?-i:[{LETRAS_OCR}])(?=[.,]?\d))" # começa com dígito ou letra equivalente OCR, e depois disso vem número (com ou sem ponto ou vírgula)
    rf"(?:[\d.]|(?-i:[{LETRAS_OCR}])(?=\d)|,(?=\d))*" # e depois do primeiro, podemos ter 0 ou mais da ordem (num ou ponto ou LETRAS_OCR SE seguido de num ou virgula SE seguido de num)
)

def norma_canonica(nome: str) -> str:
    s = sem_acento(nome)

    m = re.search(rf"complementar\D{{0,10}}?({NUM_ARTIGO})", nome, re.IGNORECASE) # "nº 64", "nº G4" (OCR)
    if m:
        return f"LC{digitos_ocr(m.group(1))}"

    m = re.search(rf"lei\D{{0,10}}?({NUM_ARTIGO})", nome, re.IGNORECASE)
    if m:
        numero = digitos_ocr(m.group(1))

        return LEI_POR_NUMERO.get(numero, f"LEI{numero}")

    for pedaco, sigla in LEI_POR_NOME.items():
        if re.search(rf"\b{pedaco}", s):
            return sigla

    return "?"

def chave_lei(trecho: str) -> tuple[str, int] | None:
    m = re.match(rf"art\w*\.?\s*({NUM_ARTIGO})", trecho, re.IGNORECASE)

    if not m:
        return None

    artigo = int(digitos_ocr(m.group(1)))

    norma = re.split(r"\s+d[oa]\s+", trecho, maxsplit=1)[1]
    return (norma_canonica(norma), artigo)

def digitos_ocr(s: str) -> str:
    return so_digitos(s.translate(OCR_PARA_DIGITO))


CLASSES = [
    (r"agravo interno|agint|ag\.? ?int", "AGINT"),
    (r"agravo regimental|agrg|ag\.? ?reg|\bagr\b", "AGRG"),
    (r"embargos de divergencia|emb\.? ?div|\beresp\b", "EDIV"),
    (r"embargos de declaracao|emb\.? ?decl|edcl|\beds?\b", "ED"),
    (r"agravo em recurso especial|a\.?resp|agresp", "ARESP"),
    (r"recurso especial eleitoral|respe", "RESPE"),
    (r"recurso especial|\bresp\b|rec\.? ?esp|r\.esp", "RESP"),
    (r"recurso em habeas corpus|\brhc\b", "RHC"),
    (r"habeas corpus|\bh\.?c\b", "HC"),
    (r"reclamacao|\brcl\b|\brecl\b", "RCL"),
    (r"recurso extraordinario com agravo|\bare\b", "ARE"),
    (r"recurso extraordinario|\bre\b", "RE"),
    (r"recurso em mandado de seguranca|\brms\b", "RMS"),
    (r"apelacao|\bapl\b", "APL"),
    (r"recurso em sentido estrito|\brse\b", "RSE"),
    (r"agravo de instrumento|\bai\b", "AI"),
]


def classes_processuais(s: str) -> set[str]:
    s = sem_acento(s)
    siglas = set()

    for padrao, sigla in CLASSES:
        if re.search(padrao, s):
            siglas.add(sigla)

            s = re.sub(padrao, " ", s)

    return siglas