import argparse
import csv
import json
from pathlib import Path

from classificar import classificar_juris, classificar_lei
from extrair_juris import extrair_juris
from extrair_leis import extrair
from resolver import DB, carregar_indice, carregar_leis, carregar_sumulas


def encode(doc: dict) -> str:
    partes = []
    for c in doc["citacoes"]:
        id_canonico = str((c.get("resolucao") or {}).get("id_canonico") or "").strip() or "-"
        conf = "-" if c.get("confianca") is None else f"{float(c['confianca']):.4f}"
        partes.append(f"{int(c['inicio'])},{int(c['fim'])},{c['classificacao']},{id_canonico},{conf}")
    return "|".join(partes) or "-"


def _processar(documento_id: str, texto: str, leis: dict, indice: dict, sumulas: dict) -> dict:
    citacoes = [classificar_lei(c, leis) for c in extrair(texto)]
    citacoes += [classificar_juris(c, indice, sumulas) for c in extrair_juris(texto)]

    return {"documento_id": documento_id, "citacoes": citacoes}


def carregar_recursos(db: Path = DB) -> tuple[dict, dict, dict]:
    if not db.is_file():
        raise SystemExit(f"base não encontrada: {db}")  # sqlite3.connect criaria um .db vazio
    return carregar_leis(db), carregar_indice(db), carregar_sumulas(db)


def ler_textos(pasta: Path) -> list[tuple[str, str]]:
    return [(txt.stem, txt.open(encoding="utf-8", newline="").read()) for txt in sorted(pasta.glob("*.txt"))]


def processar_textos(textos: list[tuple[str, str]], recursos: tuple) -> list[dict]:
    return [_processar(stem, texto, *recursos) for stem, texto in textos]


def main() -> None:
    args = argparse.ArgumentParser(description="Gera a submissão a partir dos .txt e do .db.")
    args.add_argument("pasta", nargs="?", type=Path, default=Path("data/txt"))
    args.add_argument("--db", type=Path, default=DB)
    args.add_argument("--saida", type=Path, default=Path("out/submission.csv"))
    a = args.parse_args()

    pasta_json = a.saida.parent / "json"
    pasta_json.mkdir(parents=True, exist_ok=True)

    docs = processar_textos(ler_textos(a.pasta), carregar_recursos(a.db))

    for doc in docs:
        (pasta_json / f"{doc['documento_id']}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    with a.saida.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["documento_id", "citacoes"])
        w.writerows((doc["documento_id"], encode(doc)) for doc in docs)
        
    print(f"{a.saida}: {len(docs)} documentos")


if __name__ == "__main__":
    main()
