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


def processar(documento_id: str, texto: str, leis: dict, indice: dict, sumulas: dict) -> dict:
    citacoes = []

    for c in extrair(texto):
        if c["tipo"] == "lei":
            citacoes.append(classificar_lei(c, leis))

    for c in extrair_juris(texto):
        citacoes.append(classificar_juris(c, indice, sumulas))

    return {"documento_id": documento_id, "citacoes": citacoes}

def main() -> None:
    pasta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/txt")
    saida = Path("out/json")
    saida.mkdir(parents=True, exist_ok=True)

    leis = carregar_leis()
    indice = carregar_indice()
    sumulas = carregar_sumulas()

    linhas = []
    for txt in sorted(pasta.glob("*.txt")):
        texto = txt.read_text(encoding="utf-8")
        doc = processar(txt.stem, texto, leis, indice, sumulas)

        (saida / f"{txt.stem}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        linhas.append((txt.stem, encode(doc)))

    with open("out/submission.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["documento_id", "citacoes"])
        w.writerows(linhas)
    print(f"out/submission.csv: {len(linhas)} documentos")


if __name__ == "__main__":
    main()