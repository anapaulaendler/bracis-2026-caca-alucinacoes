import csv
import json
import sys
from pathlib import Path

from classificar import classificar_juris, classificar_lei
from extrair_juris import extrair_juris
from extrair_leis import extrair
from resolver import carregar_indice, carregar_leis, carregar_sumulas

sys.path.insert(0, str(Path(__file__).parent / "data"))
from json_to_submission import encode  # noqa: E402


def _processar(documento_id: str, texto: str, leis: dict, indice: dict, sumulas: dict) -> dict:
    citacoes = [classificar_lei(c, leis) for c in extrair(texto)]
    citacoes += [classificar_juris(c, indice, sumulas) for c in extrair_juris(texto)]

    return {"documento_id": documento_id, "citacoes": citacoes}


def carregar_recursos() -> tuple[dict, dict, dict]:
    return carregar_leis(), carregar_indice(), carregar_sumulas()


def ler_textos(pasta: Path) -> list[tuple[str, str]]:
    return [(txt.stem, txt.read_text(encoding="utf-8")) for txt in sorted(pasta.glob("*.txt"))]


def processar_textos(textos: list[tuple[str, str]], recursos: tuple) -> list[dict]:
    return [_processar(stem, texto, *recursos) for stem, texto in textos]


def main() -> None:
    pasta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/txt")
    saida = Path("out/json")
    saida.mkdir(parents=True, exist_ok=True)

    docs = processar_textos(ler_textos(pasta), carregar_recursos())

    for doc in docs:
        (saida / f"{doc['documento_id']}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    with open("out/submission.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["documento_id", "citacoes"])
        w.writerows((doc["documento_id"], encode(doc)) for doc in docs)
        
    print(f"out/submission.csv: {len(docs)} documentos")


if __name__ == "__main__":
    main()