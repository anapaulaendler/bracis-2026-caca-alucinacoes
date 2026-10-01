import re

from normalizar import LETRAS_OCR, NUM_ARTIGO

ANO = rf"(?-i:[\d{LETRAS_OCR}]){{2}}(?:(?-i:[\d{LETRAS_OCR}]){{2}})?(?!\d)" # "2015", "20I5", "97"

# nome das normas que aparecem depois de "do/da"
NORMAS = [
    rf"Lei\s+Complementar\s+n[º°o.]?\s*{NUM_ARTIGO}/{ANO}", # "13,105" / "l3.105"
    rf"(?:Decreto-)?Lei\s+n[º°o.]?\s*{NUM_ARTIGO}/{ANO}", # \s*: "nº\r\n13.105" (CRLF)
    r"Constitui\w+\s+(?:F\w+|da\s+Rep\w+)", # bem quebrado pensando em erros de OCR, como "Fedcral"
    r"C[óo]digo\s+de\s+Processo\s+(?:Civil|Penal)",
    r"C[óo]digo\s+de\s+Defesa\s+do\s+Consumidor",
    r"C[óo]digo\s+Penal\s+Militar",
    r"C[óo]digo\s+(?:Civil|Penal|Eleitoral)",
    r"C[óo]digo\s+Tribut[áa]rio\s+Nacional",
    r"C[óo]digo\s+de\s+Tr[âa]nsito\s+Brasileiro",
    r"Estatuto\s+da\s+Crian[çc]a\s+e\s+do\s+Adolescente",
    r"Lei\s+de\s+Execu[çc][ãa]o\s+Penal",
    r"Lei\s+de\s+Introdu[çc][ãa]o\s+[àa]s\s+Normas\s+do\s+Direito\s+Brasileiro",
    r"Lei\s+Maria\s+da\s+Penha",
    r"Lei\s+das\s+Elei[çc][õo]es",
    r"Consolida\w+\s+das\s+Leis\s+do\s+Trabalho",
    r"(?:CPC|CPP|CPM|CLT|CDC|CTN|ECA|LEP|CTB|LINDB|CF(?:/88)?|CP)(?!\w)",
]

RE_LEI = re.compile(
    r"art(?:igo|\.)?\s*" # "art." / "artigo" / "art"
    + NUM_ARTIGO + r"[º°o]?" # 5º, 373, 1.134, 1,134, B96
    r"(?:,\s*[^,\n]{1,15}?)*?" # complementos: ", I", ", § 1º-A", ", 'g'"
    r",?\s+d[oa]\s+" # " do " / ", da "
    r"(?:" + "|".join(NORMAS) + r")",
    re.IGNORECASE,
)

def extrair(texto: str) -> list[dict]:
    citacoes = []

    for m in RE_LEI.finditer(texto):
        citacoes.append({"inicio": m.start(), "fim": m.end(), "trecho": m.group(0), "tipo": "lei"})

    return citacoes