from pathlib import Path
import random
import statistics
import sys
import unicodedata


TROCAS = {"0": "O", "1": "lI", "5": "S", "6": "G", "8": "B", "9": "g", "º": "o°"}
TAXAS = [0, 0.05, 0.1, 0.2, 0.3]
SEEDS = [1, 2, 3]


def perturbar(texto: str, taxa: float, seed: int) -> str:
    rng = random.Random(seed)
    saida = list(texto)

    for i, c in enumerate(texto):
        if c == "." and 0 < i < len(texto) - 1 and texto[i - 1].isdigit() and texto[i + 1].isdigit():
            opcoes = ","

        else:
            base = unicodedata.normalize("NFD", c)[0] # á -> a
            opcoes = TROCAS.get(c) or (base if base != c else "")

        if opcoes and rng.random() < taxa:
            saida[i] = rng.choice(opcoes)

    return "".join(saida)


def perturbar_todos(textos: list[tuple[str, str]], taxa: float, seed: int) -> list[tuple[str, str]]:
    return [(stem, perturbar(texto, taxa, seed * 1000 + n)) for n, (stem, texto) in enumerate(textos)]


def media(valores: list[float]) -> float:
    return statistics.fmean(valores) if valores else float ("nan")


def main() -> None:
    from avaliar import carregar_solution, pontuar
    from main import carregar_recursos, ler_textos, processar_textos

    recursos, solution = carregar_recursos(), carregar_solution()
    textos = ler_textos(Path(__file__).parent / "data" / "txt")

    print("| taxa | score final | macro-F1 N1 | macro-F1 N2 | F1 real | F1 inventada | F1 incompleta | tau | rejeitadas |")

    for taxa in TAXAS:
        ok = []

        for seed in SEEDS:
            r = pontuar(processar_textos(perturbar_todos(textos, taxa, seed), recursos), solution)
        
            if "rejeitada" in r:
                print(f"taxa={taxa} seed={seed}: submissão REJEITADA: {r['rejeitada']}", file=sys.stderr)
            else:
                ok.append(r)

        def nivel(n, campo):
            return media([r["niveis"][n][campo] for r in ok])

        def f1(classe):
            return media([statistics.fmean(v["f1_por_classe"][classe] for v in r["niveis"].values()) for r in ok])

        tau = media([statistics.fmean(v["tau"] for v in r["niveis"].values()) for r in ok])
        
        print(f"| {taxa:.2f} | {media([r['score_final'] for r in ok]):.4f} "
              f"| {nivel(1, 'macro_f1'):.4f} | {nivel(2, 'macro_f1'):.4f} "
              f"| {f1('real'):.3f} | {f1('inventada'):.3f} | {f1('incompleta'):.3f} "
              f"| {tau:.3f} | {len(SEEDS) - len(ok)} |")


if __name__ == "__main__":
    main()