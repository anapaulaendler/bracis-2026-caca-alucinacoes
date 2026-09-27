import csv
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "data"))
from kaggle_metric import avaliar  # noqa: E402

GABARITO = Path(__file__).parent / "data" / "goldenset_offsets.csv"


def carregar_solution() -> pd.DataFrame:
    por_doc = defaultdict(list)

    nivel = {}

    with GABARITO.open(encoding="utf-8-sig") as f:
        for g in csv.DictReader(f):
            doc_ids = g["id_canonico"].strip() or "-"
            por_doc[g["documento_id"]].append(f"{g['inicio']},{g['fim']},{g['classificacao']},{doc_ids}")
            nivel[g["documento_id"]] = int(g["nivel"])

    for txt in (GABARITO.parent / "txt").glob("*.txt"):
        doc = txt.stem
        nivel.setdefault(doc, 1 if "_n1_" in doc else 2)

    linhas = [(doc, nivel[doc], "|".join(por_doc[doc]) or "-") for doc in sorted(nivel)]

    return pd.DataFrame(linhas, columns=["documento_id", "nivel", "citacoes"])


def main() -> None:
    caminho = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("out/submission.csv")
    sub = pd.read_csv(caminho, dtype=str, keep_default_na=False)
    r = avaliar(carregar_solution(), sub)

    for nivel, d in r["niveis"].items():
        f1 = "  ".join(f"{c}={v:.2f}" for c, v in d["f1_por_classe"].items())
        print(f"nível {nivel}: score={d['score']:.4f}  macroF1={d['macro_f1']:.4f}  "f"tau={d['tau']:.2f}  [{f1}]")
    print(f"SCORE FINAL: {r['score_final']:.4f}   (máximo 1.1000)")


if __name__ == "__main__":
    main()
