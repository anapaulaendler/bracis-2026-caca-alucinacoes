from pathlib import Path

from extrair_juris import extrair_juris
from extrair_leis import extrair
from normalizar import chave_lei, classes_processuais, digitos_ocr, norma_canonica


def test_extrai_lei_com_incisos():
    casos = {
        "conforme o art. 5º, LV, da Constituição Federal, o réu": ("art. 5º, LV, da Constituição Federal", ("CF", 5)),
        "o art. 373, I, do CPC impõe": ("art. 373, I, do CPC", ("CPC", 373)),
        "art. 1.134 do Código Civil": ("art. 1.134 do Código Civil", ("CC", 1134)),
    }
    for texto, (trecho, chave) in casos.items():
        (c,) = extrair(texto)
        assert c["trecho"] == trecho, c
        assert chave_lei(c["trecho"]) == chave


def test_extrai_lei_com_ruido_de_ocr():
    (c,) = extrair("nos termos do artigo 7º, XXIX, da Constituição Fedcral.")
    assert chave_lei(c["trecho"]) == ("CF", 7)


def test_norma_canonica():
    casos = {
        "Lei nº 8.078/1990": "CDC",
        "Lei Complementar nº 64/1990": "LC64",
        "Lei nº 9.504/1997": "LEI9504",
        "Código Civil": "CC",
        "Código de Processo Penal": "CPP",
        "Consolidação das Leis do Trabalho": "CLT",
        "CLT": "CLT",
        "Estatuto da Cidade": "?",
    }
    for nome, sigla in casos.items():
        assert norma_canonica(nome) == sigla, nome


def test_digitos_ocr():
    assert digitos_ocr("2O16.Ol5-6") == "20160156"


def test_classes_processuais():
    assert classes_processuais("AgInt no REsp") == {"AGINT", "RESP"}
    assert classes_processuais("Recurso em Habeas Corpus") == {"RHC"}


def test_extrai_juris_todas_as_formas():
    texto = ("Aplica-se a Súmula 7 do STJ. Ver Tema 1.046 da repercussão geral. "
             "Diverge do precedente do STF de 2024, da relatoria de Cármen Lúcia. "
             "Não destoa o RE. nº 3.647.129-RS. Também o AgInt no REsp 1.234.567/SP.")
    achados = [(c["forma"], c["trecho"]) for c in extrair_juris(texto)]
    assert achados == [
        ("sumula", "Súmula 7 do STJ"),
        ("tema", "Tema 1.046 da repercussão geral"),
        ("vaga", "precedente do STF de 2024, da relatoria de Cármen Lúcia"),
        ("processo", "RE. nº 3.647.129-RS"),
        ("processo", "AgInt no REsp 1.234.567/SP"),
    ]


def test_trecho_bate_com_offsets():
    texto = ("O art. 5º, LV, da Constituição Federal e a Súmula 7 do STJ,\n"
             "além do RE. nº 3.647.129-RS, resolvem.")
    for c in extrair(texto) + extrair_juris(texto):
        assert texto[c["inicio"]:c["fim"]] == c["trecho"], c


if __name__ == "__main__":
    for nome, teste in list(globals().items()):
        if nome.startswith("test_"):
            teste()
            print("ok", nome)
