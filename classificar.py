import re

from extrair_juris import RE_NUMERO
from normalizar import chave_lei, classes_processuais, digitos_ocr


def _real(citacao, doc_id, confianca):
    return {**citacao, "classificacao": "real", "resolucao": {"id_canonico": str(doc_id)},
            "confianca": confianca}


def _sem_link(citacao, classe, confianca):
    return {**citacao, "classificacao": classe, "resolucao": None, "confianca": confianca}


def classificar_lei(citacao: dict, leis: dict) -> dict:
    chave = chave_lei(citacao["trecho"])
    doc_id = leis.get(chave)

    if doc_id is not None:
        return {**citacao, "classificacao": "real", "resolucao": {"id_canonico": str(doc_id)}, "confianca": 0.95}

    return {**citacao, "classificacao": "inventada", "resolucao": None, "confianca": 0.85}

def classificar_juris(citacao: dict, indice: dict, sumulas: dict) -> dict:
    forma, trecho = citacao["forma"], citacao["trecho"]

    if forma == "vaga":
        return _sem_link(citacao, "incompleta", 0.9)

    if forma == "tema":
        return _sem_link(citacao, "inventada", 0.8)

    if forma == "sumula":
        vinculante = "vinculante" in trecho.lower()
        numero = int(re.search(r"\b\d+\b", trecho).group(0)) # type: ignore
        
        achou = sumulas.get((vinculante, numero))
        tribunal_citado = re.search(r"STF|STJ|TST|TSE", trecho)
        
        if achou and (not tribunal_citado or tribunal_citado.group(0) == achou[1]):
            return _real(citacao, achou[0], 0.95)
        
        return _sem_link(citacao, "inventada", 0.9)

    numeros = [m.group(0) for m in RE_NUMERO.finditer(trecho)]
    candidatos = indice.get(digitos_ocr(max(numeros, key=len)), [])

    if not candidatos:
        return _sem_link(citacao, "inventada", 0.9)

    feitos = list({c["cabecalho"]: c for c in candidatos}.values())
    if len(feitos) == 1:
        return _real(citacao, feitos[0]["id"], 0.95)

    classes_cit = classes_processuais(trecho)
    notas = sorted(((len(classes_cit & f["classes"]) / max(1, len(classes_cit | f["classes"])), f["id"])
                    for f in feitos), reverse=True)

    if notas[0][0] > notas[1][0]:
        return _real(citacao, notas[0][1], 0.75)
    return _sem_link(citacao, "incompleta", 0.6)