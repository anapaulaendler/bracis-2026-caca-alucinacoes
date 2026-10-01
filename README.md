# Caça-Alucinações: verificador de citações jurídicas

Solução para o desafio **Jusbrasil × BRACIS 2026**. O sistema lê um parecer jurídico gerado por LLM, encontra cada citação de jurisprudência e de lei e a classifica como:

- **real**: resolve para exatamente um registro da base canônica;
- **inventada**: tem identificadores suficientes, mas nenhum registro corresponde;
- **incompleta**: não dá para consultar, ou há empate entre candidatos.

## Pipeline

1. **Extrair** (`extrair_leis` / `extrair_juris`): lê o `.txt` e encontra as citações com regex tolerante a OCR.
2. **Normalizar** (`normalizar`): padroniza siglas e corrige dígitos trocados por OCR.
3. **Resolver** (`resolver`): consulta a base `.db` com índice por número, súmulas e dispositivos.
4. **Classificar** (`classificar`): aplica uma regra nomeada e atribui a confiança calibrada dessa regra.
5. **Exportar**: grava o resultado em JSON e gera o `submission.csv`.

## Como rodar

Os dados da competição não são redistribuídos (regras do desafio). Coloque o conteúdo do zip em `data/`.

Ponto de entrada único. O índice é reconstruído do `.db` a cada execução, então uma base nova funciona sem passo extra:

```bash
docker build -t caca-alucinacoes .
docker run --rm --network none -v /caminho/dados:/dados -v /caminho/saida:/saida \
    caca-alucinacoes /dados/base.db /dados/txt /saida/submission.csv
```

Sem Docker, basta Python 3.10+ (só biblioteca padrão, determinístico, CPU):

```bash
bash run.sh <caminho_db> <pasta_txt> <arquivo_saida>
```

Avaliação e experimentos (precisam de pandas):

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python avaliar.py          # score local com a métrica oficial
.venv/bin/python ruido.py            # régua de robustez (score × taxa de ruído)
.venv/bin/python ruido.py --ablacao  # queda por tipo de ruído
.venv/bin/python calibrar.py         # recalibra a tabela de confiança
.venv/bin/python test_citacoes.py    # 13 testes
```

## Métrica

- **Casamento:** predição e gabarito casam por IoU maior ou igual à 0.5.
- **macro-F1 das 3 classes, por nível:** uma `real` só conta como acerto se o id apontado estiver certo.
- **Penalidade `s = F1 * (1 − 0.5 * FPR)`:** FPR (o τ da métrica oficial) é a fração das inventadas preditas como reais, o erro grave de aprovar uma alucinação.
- **Bônus de calibração `b = 0.1 * (1 − Brier)`:** calculado sobre os pares casados.
- **Score final:** `(N1 + 2 * N2) / 3`, com máximo de 1.1.

## Resultados

### Conjunto de desenvolvimento (26 documentos, 192 citações)

```
nível 1: score=1.1000  macroF1=1.0000  FPR=0.00  [real=1.00  inventada=1.00  incompleta=1.00]
nível 2: score=1.0999  macroF1=1.0000  FPR=0.00  [real=1.00  inventada=1.00  incompleta=1.00]
SCORE FINAL: 1.1000   (máximo 1.1000)
```

O pipeline acerta todas as citações do conjunto de desenvolvimento desde a primeira versão. Sem erro para corrigir ali, esse conjunto **saturou**: não ajuda mais a medir generalização. Por isso as seções seguintes avaliam o pipeline sob ruído de OCR.

### Robustez a ruído de OCR sintético

`ruido.py` troca caracteres dos documentos (`0 por O`, `1 por l/I`, `5 por S`, `6 por G`, `8 por B`, `9 por g`, `º por o/°`, `á por a`, `. por ,` dentro de números), com probabilidade `taxa`, em 3 seeds. A troca 1 a 1 preserva os offsets do gabarito. A base canônica fica limpa, como no mundo real.

*Score inicial* é o da primeira versão do pipeline, antes das correções guiadas pela ablação (`ruido.py --ablacao`).

| taxa | score inicial | score final | macro-F1 N1 | macro-F1 N2 | F1 real | F1 inventada | F1 incompleta | FPR | rejeitadas |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.00 | 1.0992 | 1.1000 | 1.0000 | 1.0000 | 1.000 | 1.000 | 1.000 | 0.000 | 0 |
| 0.05 | 1.0357 | 1.0933 | 0.9965 | 0.9928 | 1.000 | 0.984 | 1.000 | 0.000 | 0 |
| 0.10 | 0.9605 | 1.0857 | 0.9880 | 0.9876 | 0.989 | 0.974 | 1.000 | 0.000 | 0 |
| 0.20 | 0.8782 | 1.0469 | 0.9582 | 0.9522 | 0.949 | 0.917 | 1.000 | 0.000 | 0 |
| 0.30 | 0.8070 | 1.0141 | 0.9122 | 0.9314 | 0.908 | 0.857 | 1.000 | 0.000 | 0 |

**FPR = 0 em todas as taxas:** mesmo com 30% dos caracteres elegíveis corrompidos, o pipeline nunca aprova uma citação inventada como real. Quando erra, erra para o lado seguro: uma citação real com o número corrompido deixa de ser encontrada e vira "inventada".

### Confiança calibrada sob ruído

Cada regra de decisão (`classificar.CONFIANCA`) usa como confiança sua acurácia sob ruído, com suavização de Laplace. Validação 2-fold (calibra numa metade, mede na outra):

| fold | Brier manual | Brier calibrada | score manual | score calibrada |
|---|---:|---:|---:|---:|
| A-B | 0.0224 | 0.0172 | 1.0714 | 1.0719 |
| B-A | 0.0162 | 0.0105 | 1.0715 | 1.0720 |

A calibração também expôs um ponto fraco: "processo não encontrado" com sinal de OCR acertava ~50%. Após as correções de extração, 84%.

## Decisões

- **Regex, não ML.** As citações têm formato regular; o erro que importa está na resolução contra a base.
- **Calibrar sob ruído.** No conjunto limpo toda regra acerta 100%; confiança 1.0 perde sob qualquer ruído.
- **UFs listadas explicitamente.** Regras genéricas para proteger a UF cortavam números como "1.S5O.OOO".

## Limitações

- O conjunto de desenvolvimento é sintético; o score local não garante o teste privado.
- Não extrai citações no plural ("arts. 186 e 927"), ausentes nos dados.
- O ruído só troca caracteres; não insere nem remove (ex.: "I 821 663" não é recuperado).
- Regras sem amostra sob ruído mantêm a confiança manual.
- Não verifica se a lei diz o que o texto afirma (fora da métrica).
