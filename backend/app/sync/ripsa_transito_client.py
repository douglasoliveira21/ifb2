"""Cliente para o indicador RIPSA MRT.4.03 (Taxa de mortalidade por lesão
de trânsito) — Ministério da Saúde, publicado como CSV no Portal de
Dados Abertos do SUS (https://dadosabertos.saude.gov.br). Mesmo padrão
de fonte já usado em `ripsa_client.py` (Razão de Mortalidade Materna),
mas um arquivo bem maior: ~1,7 milhão de linhas, uma por combinação de
UF × município × ano × sexo × faixa etária desde 2000 — o IFB soma o
numerador (óbitos) e o denominador (população estimada) de todas as
linhas de um mesmo UF+ano antes de calcular a taxa (mesma lógica de
agregação de `ripsa_client.py`: soma antes de dividir, nunca a média
das taxas municipais).

**Cabeçalhos com bug de codificação**: o CSV de origem tem os nomes de
coluna com acentos corrompidos de um jeito diferente do bug já
documentado no SICONFI/FBSP — aqui não é um caractere de substituição
("�"), é um caractere Unicode válido só que errado (ex: "trânsito"
virou "tr\xe2nsito", "â" em vez de "ã"), então usar `.decode('utf-8')`
não levanta erro nem ajuda a detectar o problema. Por isso a leitura
localiza as colunas por um prefixo ASCII estável ("Numerador - Obitos
por lesao de", sem tocar no sufixo corrompido) em vez de comparar a
string completa.

Conferido: Brasil 2024 = 17,48 por 100 mil habitantes — mesma ordem de
grandeza das ~37 mil mortes no trânsito por ano já amplamente
noticiadas para o Brasil.
"""
import csv
import io
import zipfile
from collections import defaultdict
from datetime import date

import httpx

from app.sync.bcb_client import SeriesPoint

REQUEST_HEADERS = {
    "User-Agent": "IFB-Sync/1.0 (+https://github.com/douglasoliveira21/ifb2)",
}

TAXA_TRANSITO_URL = "https://demas-dados-abertos.s3.amazonaws.com/csv/mgdi_ms_g0g.csv.zip"


def _resolve_columns(fieldnames: list[str]) -> dict[str, str]:
    numerador = next(f for f in fieldnames if f.startswith("Numerador - Obitos por lesao de"))
    denominador = next(f for f in fieldnames if "Denominador" in f and "Popula" in f)
    return {"uf": "UF", "ano": "Ano", "numerador": numerador, "denominador": denominador, "fator": "Multiplicador"}


def _download_rows(url: str, *, timeout: float):
    response = httpx.get(url, headers=REQUEST_HEADERS, timeout=timeout, follow_redirects=True)
    response.raise_for_status()
    zf = zipfile.ZipFile(io.BytesIO(response.content))
    with zf.open(zf.namelist()[0]) as f:
        text = f.read().decode("utf-8")
    return csv.DictReader(io.StringIO(text))


def _aggregate(url: str, *, timeout: float) -> dict[tuple[str, int], tuple[float, float, float]]:
    """Retorna {(uf, ano): (soma_numerador, soma_denominador, fator)}."""
    reader = _download_rows(url, timeout=timeout)
    cols = _resolve_columns(reader.fieldnames or [])

    totals: dict[tuple[str, int], list[float]] = defaultdict(lambda: [0.0, 0.0, 100000.0])
    for row in reader:
        try:
            uf = row[cols["uf"]]
            year = int(row[cols["ano"]])
            numerador = float(row[cols["numerador"]])
            denominador = float(row[cols["denominador"]])
            fator = float(row[cols["fator"]])
        except (KeyError, ValueError):
            continue
        entry = totals[(uf, year)]
        entry[0] += numerador
        entry[1] += denominador
        entry[2] = fator

    return {key: tuple(value) for key, value in totals.items()}


def fetch_taxa_mortalidade_transito_by_state(
    url: str = TAXA_TRANSITO_URL, *, timeout: float = 120.0
) -> dict[str, list[SeriesPoint]]:
    totals = _aggregate(url, timeout=timeout)

    by_state: dict[str, list[SeriesPoint]] = defaultdict(list)
    for (uf, year), (num, den, fator) in totals.items():
        if den <= 0:
            continue
        by_state[uf].append(SeriesPoint(reference_date=date(year, 12, 31), value=(num / den) * fator))

    for points in by_state.values():
        points.sort(key=lambda p: p.reference_date)
    return dict(by_state)


def fetch_taxa_mortalidade_transito_brasil(
    url: str = TAXA_TRANSITO_URL, *, timeout: float = 120.0
) -> list[SeriesPoint]:
    totals = _aggregate(url, timeout=timeout)

    by_year: dict[int, list[float]] = defaultdict(lambda: [0.0, 0.0, 100000.0])
    for (_uf, year), (num, den, fator) in totals.items():
        entry = by_year[year]
        entry[0] += num
        entry[1] += den
        entry[2] = fator

    points = [
        SeriesPoint(reference_date=date(year, 12, 31), value=(num / den) * fator)
        for year, (num, den, fator) in by_year.items()
        if den > 0
    ]
    points.sort(key=lambda p: p.reference_date)
    return points
