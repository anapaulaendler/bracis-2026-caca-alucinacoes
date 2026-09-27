from normalizar import chave_lei


def classificar_lei(citacao: dict, leis: dict) -> dict:
    chave = chave_lei(citacao["trecho"])
    doc_id = leis.get(chave)

    if doc_id is not None:
        return {**citacao, "classificacao": "real", "resolucao": {"id_canonico": str(doc_id)}, "confianca": 0.95}

    return {**citacao, "classificacao": "inventada", "resolucao": None, "confianca": 0.85}