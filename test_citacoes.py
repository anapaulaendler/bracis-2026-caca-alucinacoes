from pathlib import Path

from extrair_juris import extrair_juris
from extrair_leis import extrair
from normalizar import chave_lei, classes_processuais, digitos_ocr, norma_canonica

DADOS = (Path(__file__).parent / "data" / "kaggle_metric.py").exists()


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


def test_carregar_leis_pula_dispositivo_fora_do_padrao():
    import sqlite3
    import tempfile

    from resolver import carregar_leis

    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "mini.db"
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE documentos (id INTEGER, natureza TEXT, tribunal TEXT, texto TEXT)")
        con.executemany("INSERT INTO documentos VALUES (?, ?, ?, ?)", [
            (1, "dispositivo", None, "Artigo 5º da Constituição Federal de 1988"),
            (2, "dispositivo", None, "texto sem o cabeçalho esperado"),
        ])
        con.commit()
        con.close()
        assert carregar_leis(db) == {("CF", 5): 1}


def _cit(trecho, forma=None):
    c = {"inicio": 0, "fim": len(trecho), "trecho": trecho}
    return {**c, "forma": forma} if forma else c


def test_classificar_lei():
    from classificar import classificar_lei

    leis = {("CF", 5): 123}

    r = classificar_lei(_cit("art. 5º, LV, da Constituição Federal"), leis)
    assert (r["classificacao"], r["resolucao"], r["regra"]) == ("real", {"id_canonico": "123"}, "lei_resolvida")
    
    r = classificar_lei(_cit("art. 999 da Constituição Federal"), leis)
    assert (r["classificacao"], r["regra"]) == ("inventada", "lei_nao_achada")
    
    r = classificar_lei(_cit("art. 1 do Estatuto da Cidade"), leis)
    assert (r["classificacao"], r["resolucao"], r["regra"]) == ("incompleta", None, "lei_norma_desconhecida")


def test_classificar_juris():
    from classificar import classificar_juris

    sumulas = {(False, 7): (99, "STJ")}
    
    indice = {
        "3647129": [{"id": 5, "classes": {"RE"}, "cabecalho": "a"}],
        "1234567": [{"id": 6, "classes": {"AGINT", "RESP"}, "cabecalho": "b"}, {"id": 7, "classes": {"HC"}, "cabecalho": "c"}],
        "7654321": [{"id": 8, "classes": {"HC"}, "cabecalho": "d"}, {"id": 9, "classes": {"HC"}, "cabecalho": "e"}],
    }

    casos = [
        (_cit("precedente do STF de 2024, da relatoria de Cármen Lúcia", "vaga"), "incompleta", None, "vaga"),
        (_cit("Tema 1.046 da repercussão geral", "tema"), "inventada", None, "tema"),
        (_cit("Súmula 7 do STJ", "sumula"), "real", "99", "sumula_ok"),
        (_cit("Súmula 7 do STF", "sumula"), "inventada", None, "sumula_nao_achada"),
        (_cit("RE. nº 3.647.129-RS", "processo"), "real", "5", "processo_unico"),
        (_cit("AgInt no REsp 1.234.567/SP", "processo"), "real", "6", "processo_desempate"),
        (_cit("REsp 7.654.321/SP", "processo"), "incompleta", None, "processo_empate"),
        (_cit("REsp 1.111.111/SP", "processo"), "inventada", None, "processo_nao_achado"),
    ]
    
    for citacao, classe, doc_id, regra in casos:
        r = classificar_juris(citacao, indice, sumulas)
        
        got_id = r["resolucao"]["id_canonico"] if r["resolucao"] else None
        
        assert (r["classificacao"], got_id, r["regra"]) == (classe, doc_id, regra), (citacao["trecho"], r)


if __name__ == "__main__":
    for nome, teste in list(globals().items()):
        if nome.startswith("test_"):
            teste()
            print("ok", nome)
            
    if not DADOS:
        print("aviso: data/ ausente — testes dependentes de dados retornaram cedo")
