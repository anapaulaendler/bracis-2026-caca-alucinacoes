import re

from extrair_juris import RE_NUMERO
from normalizar import chave_lei, classes_processuais, digitos_ocr

# TODO: calibrar.py
CONFIANCA = {
    "lei_resolvida": 0.95,
    "lei_nao_achada": 0.85,
    "lei_norma_desconhecida": 0.6,
    "vaga": 0.9,
    "tema": 0.8,
    "sumula_ok": 0.95,
    "sumula_nao_achada": 0.9,
    "processo_nao_achado": 0.9,
    "processo_unico": 0.95,
    "processo_desempate": 0.75,
    "processo_empate": 0.6,
}


def _real(citacao, regra, doc_id):
    return {**citacao, "classificacao": "real", "resolucao": {"id_canonico": str(doc_id)}, "confianca": CONFIANCA[regra], "regra": regra}


def _sem_link(citacao, regra, classe):
    return {**citacao, "classificacao": classe, "resolucao": None, "confianca": CONFIANCA[regra], "regra": regra}


def classificar_lei(citacao: dict, leis: dict) -> dict:
    chave = chave_lei(citacao["trecho"])

    if chave is None or chave[0] == "?":
        return _sem_link(citacao, "lei_norma_desconhecida", "incompleta") # não há como consultar

    doc_id = leis.get(chave)
    if doc_id is not None:
        return _real(citacao, "lei_resolvida", doc_id)

    return _sem_link(citacao, "lei_nao_achada", "inventada")


def classificar_juris(citacao: dict, indice: dict, sumulas: dict) -> dict:
    forma, trecho = citacao["forma"], citacao["trecho"]

    if forma == "vaga":
        return _sem_link(citacao, "vaga", "incompleta")

    if forma == "tema":
        return _sem_link(citacao, "tema", "inventada")

    if forma == "sumula":
        vinculante = "vinculante" in trecho.lower()
        numero = int(digitos_ocr(re.search(r"m(?:ula|\.)\s+(?:vinculante\s+)?(?:n[º°.]?\s*)?(\S+)", trecho, re.I).group(1)))  # type: ignore
        
        achou = sumulas.get((vinculante, numero))
        tribunal_citado = re.search(r"STF|STJ|TST|TSE", trecho)
        
        if achou and (not tribunal_citado or tribunal_citado.group(0) == achou[1]):
            return _real(citacao, "sumula_ok", achou[0])

        return _sem_link(citacao, "sumula_nao_achada", "inventada")

    numeros = [m.group(0) for m in RE_NUMERO.finditer(trecho)]
    candidatos = indice.get(digitos_ocr(max(numeros, key=len)), [])

    if not candidatos:
        return _sem_link(citacao, "processo_nao_achado", "inventada")

    feitos = list({c["cabecalho"]: c for c in candidatos}.values())
    if len(feitos) == 1:
        return _real(citacao, "processo_unico", feitos[0]["id"])

    classes_cit = classes_processuais(trecho)
    notas = sorted(((len(classes_cit & f["classes"]) / max(1, len(classes_cit | f["classes"])), f["id"])
                    for f in feitos), reverse=True)

    if notas[0][0] > notas[1][0]:
        return _real(citacao, "processo_desempate", notas[0][1])
    
    return _sem_link(citacao, "processo_empate", "incompleta")