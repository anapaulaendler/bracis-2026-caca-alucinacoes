
"""calibra a confiança (do classificar.py) utilizando a acurácia de cada regra sob ruído de OCR.
"""
from collections import defaultdict
from pathlib import Path
from typing import Counter

from avaliar import carregar_solution, pontuar
from classificar import CONFIANCA
from kaggle_metric import _casar, _norm_id, _parse_solution_cell
from main import carregar_recursos, ler_textos, processar_textos
from ruido import TAXAS, media, perturbar_todos


SEEDS_CALIBRAR = [11, 12, 13]
SEEDS_AVALIAR = [21, 22, 23]


def metades(textos: list[tuple[str, str]]) -> tuple[list, list]:
    a, b = [], []

    for nivel in ("_n1_", "_n2_"): # níveis do gabarito
        do_nivel = [(nome, texto) for nome, texto in textos if nivel in nome]

        for posicao, doc in enumerate(do_nivel):
            if posicao % 2 == 0: 
                a.append(doc)
            else:
                b.append(doc)

    return a, b


def rodar(textos, seeds, recursos) -> list[list[dict]]:
    return [processar_textos(perturbar_todos(textos, taxa, s), recursos) for taxa in TAXAS for s in seeds]


def acertos_por_citacao(rodadas: list[list[dict]], solution) -> list[tuple[str, int, float]]:
    gabarito = dict(zip(solution["documento_id"], solution["citacoes"]))
    resultado = []

    for docs in rodadas:
        for doc in docs:
            esperadas = _parse_solution_cell(gabarito[doc["documento_id"]], doc["documento_id"])
            previstas = doc["citacoes"]

            pares_casados, _, _ = _casar(esperadas, previstas)

            for i_esperada, i_prevista in pares_casados:
                esperada, prevista = esperadas[i_esperada], previstas[i_prevista]

                classe_certa = prevista["classificacao"] == esperada["classe"]
                
                link_certo = esperada["classe"] != "real" or (prevista["resolucao"] is not None and _norm_id(prevista["resolucao"]["id_canonico"]) in esperada["doc_ids"])

                resultado.append((prevista["regra"], int(classe_certa and link_certo), prevista["confianca"]))

    return resultado


def calibrar(pares: list[tuple[str, int, float]]) -> dict[str, float]:
    soma, n = defaultdict(int), defaultdict(int)

    for regra, y, _ in pares:
        soma[regra] += y
        n[regra] += 1

    return {regra: (soma[regra] + 1) / (n[regra] + 2) for regra in n} 


def brier(pares: list[tuple[str, int, float]]) -> float:
    return media([(confianca - y) ** 2 for _, y, confianca in pares])


def aplicar(tabela: dict[str, float], rodadas: list[list[dict]]) -> None:
    for docs in rodadas:
        for doc in docs:
            for citacao in doc["citacoes"]:
                citacao["confianca"] = tabela.get(citacao["regra"], citacao["confianca"])


def score_medio(rodadas, solution) -> float:
    return media([resultado["score_final"] for resultado in (pontuar(docs, solution) for docs in rodadas) if "score_final" in resultado])

    
def main() -> None:
    recursos, solution = carregar_recursos(), carregar_solution()
    textos = ler_textos(Path(__file__).parent / "data" / "txt")
    a, b = metades(textos)

    print("| fold | Brier antes | Brier depois | score antes | score depois |")
    print("|---|---:|---:|---:|---:|")

    for nome, calibragem, avaliacao in (("A-B", a, b), ("B-A", b, a)):
        tabela = calibrar(acertos_por_citacao(rodar(calibragem, SEEDS_CALIBRAR, recursos), solution))
        rodadas = rodar(avaliacao, SEEDS_AVALIAR, recursos)

        antes = brier(acertos_por_citacao(rodadas, solution)), score_medio(rodadas, solution)
        
        aplicar(tabela, rodadas)
        depois = brier(acertos_por_citacao(rodadas, solution)), score_medio(rodadas, solution)

        print(f"| {nome} | {antes[0]:.4f} | {depois[0]:.4f} | {antes[1]:.4f} | {depois[1]:.4f} |")

    pares = acertos_por_citacao(rodar(textos, SEEDS_CALIBRAR, recursos), solution)
    final, contagem = calibrar(pares), Counter(regra for regra, _, _ in pares)

    print("\nCONFIANCA = {")

    for regra, atual in CONFIANCA.items():
        nota = f"# n={contagem[regra]}" if regra in final else "  # sem amostra sob ruído: mantido"
        print(f'"{regra}": {final.get(regra, atual):.3f},{nota}')

    print("}")


if __name__ == "__main__":
    main()