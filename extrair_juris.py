import re

from normalizar import LETRAS_OCR, sem_acento

PALAVRA_CLASSE = re.compile(
    r"(?:REsp|R\.Esp|Rec|Esp|Recurso|Especial|Eleitoral|Agravo|Ag|AgInt|Int|"
    r"AgRg|AgR|EDcl|EDs?|Embargos|Declaracao|Interno|Regimental|Instrumento|"
    r"Rcl|Recl|Reclamacao|RHC|HC|H\.C|Habeas|Corpus|APL|RSE|A\.?REsp|AREspEl|"
    r"REspe|AgREsp|RMS|Mandado|Seguranca|RE|AI|AR|Suspensao|Liminar|Sentenca|"
    r"Terceiro|AG\.REG|"
    r"[A-Z]{1,5}(?:-[A-Za-z]{1,5})+-?|TST-?|" # siglas do TST: E-ED-RR, TST-ED-E-ED-RR-
    r"julgado|precedente|acordao)[.,]?",
    re.IGNORECASE,
)
CONECTORES = {"no", "na", "nos", "nas", "em", "de", "e", "do", "da", "-", "processo", "Processo"}
MARCA_NUMERO = re.compile(r"n[º°o.]?|N[º°oO]\.?")

# número com ruído de OCR
INICIO_NUM = rf"(?:\d|[{LETRAS_OCR}](?=[.,]?\d))" # dígito, ou letra de OCR com dígito logo depois ("O600530", "l.327" = sim // "Os" = não).
# número = pedaços separados por . - –; o 1º começa como INICIO_NUM, os demais são dígitos/letras de OCR
# ("700076B-37", "1.S5O.OOO") desde que não sejam uma UF ("99.942-BA", "1.234-GO" param antes da UF)
# vírgula só colada em dígito: OCR de "." ("1,327.863"), não separador de lista
UFS = "AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO"
SEP_NUM = r"(?:[.\-–]|,(?=\d))"
NUM = rf"{INICIO_NUM}[\d{LETRAS_OCR}]*(?:{SEP_NUM}+(?!(?:{UFS})(?![A-Za-z]))[\d{LETRAS_OCR}]+)*{SEP_NUM}*"
RE_NUMERO = re.compile(rf"(?<![\w/]){NUM}(?:\s{{1,2}}[.\-–]?{NUM}){{0,4}}")
RE_UF = re.compile(r"\s{0,2}[/\-–(]\s{0,2}[A-Z]{2}\)?(?![a-z])")

RE_SUMULA = re.compile(
    rf"(?:S|5)[úuÚU]m(?:ula|\.)\s+(?:Vinculante\s+)?(?:n[º°.]?\s*)?{INICIO_NUM}[\d{LETRAS_OCR}]*"
    r"(?:\s+do\s+(?:STF|STJ|TST|TSE))?",
    re.IGNORECASE,
)
RE_TEMA = re.compile(r"Tem[aãá]\s+(?:n[º°.]?\s*)?\d[\d.]*\s+da\s+repercuss\w+\s+geral", re.IGNORECASE)

TRIBUNAL = r"(?:STF|STJ|TST|TSE|STM)"
NOME = r"[A-ZÀ-Ú][\wÀ-ú]*(?:\s+(?:(?:de|da|do|dos|De|DA|DE|Dc)\s+)?[A-ZÀ-Ú][\wÀ-ú]*){0,5}"
RE_VAGA = re.compile(
    rf"(?:\s+do\s+{TRIBUNAL})?,?\s+(?:\w+\s+)?(?P<ano_kw>em|de)\s+(?:[1lI][9g]|2[0Oo])[\d{LETRAS_OCR}]{{2}},?\s+"
    rf"(?:(?:pela|sob|da)\s+relatoria\s+d[ec]|Rel\.\s+Min\.)\s+{NOME}"
)

def andar_para_esquerda(texto: str, pos: int, max_palavras: int = 12) -> tuple[int, bool]:
    janela_ini = max(0, pos - 150)
    palavras = list(re.finditer(r"\S+", texto[janela_ini:pos]))
    inicio, achou_classe = pos, False

    for n, w in enumerate(reversed(palavras)):
        tok, tok_ini = w.group(0), janela_ini + w.start()

        if tok != "-" and PALAVRA_CLASSE.fullmatch(sem_acento(tok)):
            inicio, achou_classe = tok_ini, True

        elif tok in ("processo", "Processo"):
            inicio = tok_ini

        elif tok in CONECTORES or (MARCA_NUMERO.fullmatch(tok) and not achou_classe):
            pass
        else:
            break
        if n >= max_palavras:
            break

    return inicio, achou_classe

def achar_vagas(texto):
    for m in RE_VAGA.finditer(texto):
        ini, ok = andar_para_esquerda(texto, m.start())
        if not ok:
            ini, ok = andar_para_esquerda(texto, m.start("ano_kw"))
        if ok:
            yield ini, m.end()


def achar_por_regex(texto, regex):
    for m in regex.finditer(texto):
        yield m.start(), m.end()


def achar_processos(texto):
    for m in RE_NUMERO.finditer(texto):
        span = span_do_processo(texto, m)
        if span:
            yield span


def span_do_processo(texto, m):
    num = m.group(0).rstrip(".-– \n")
    if sum(c.isdigit() for c in num) < 3:
        return None
    
    ini_num, fim = m.start(), m.start() + len(num)

    colado = ini_num
    while colado > 0 and not texto[colado - 1].isspace():
        colado -= 1

    ini, ok = andar_para_esquerda(texto, colado)
    
    if colado < ini_num:
        ini = min(ini, colado)
        ok = ok or bool(re.search(r"[A-Z]{2}", texto[colado:ini_num]))
    
    if not ok:
        return None

    uf = RE_UF.match(texto, fim)
    return ini, (uf.end() if uf else fim)


def extrair_juris(texto: str) -> list[dict]:
    buscas = [
        ("vaga", achar_vagas(texto)),
        ("sumula", achar_por_regex(texto, RE_SUMULA)),
        ("tema", achar_por_regex(texto, RE_TEMA)),
        ("processo", achar_processos(texto)),
    ]
    spans = []
    for forma, achados in buscas:
        for ini, fim in achados:
            if all(fim <= a or ini >= b for a, b, _ in spans):
                spans.append((ini, fim, forma))

    return [{"inicio": a, "fim": b, "trecho": texto[a:b], "tipo": "jurisprudencia", "forma": f}
            for a, b, f in sorted(spans)]