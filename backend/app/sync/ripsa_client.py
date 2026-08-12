"""Cliente para os indicadores pré-calculados do catálogo RIPSA (Rede
Interagencial de Informação para a Saúde) publicados como CSV no Portal
de Dados Abertos do SUS (https://dadosabertos.saude.gov.br).

Diferente da maioria das fontes do IFB, o RIPSA não tem uma API — cada
indicador é um arquivo CSV zipado hospedado em
`https://demas-dados-abertos.s3.amazonaws.com/csv/<codigo>.csv.zip`. O
código de cada indicador (ex: `ripsa001mt` para a Razão de Mortalidade
Materna, MRT.2.01) foi obtido navegando o portal manualmente — não há
um índice programático conhecido, então uma nova fonte RIPSA precisa
ser localizada e conferida à mão antes de ser adicionada aqui (mesmo
processo já usado para achar `ripsa001mt`).

O CSV já traz numerador e denominador brutos, não só a razão pronta —
o IFB soma o numerador e o denominador de todos os estados antes de
calcular a razão nacional (agregação correta para uma taxa: soma dos
óbitos sobre soma dos nascidos vivos, não a média simples das razões
estaduais, que distorceria o resultado a favor de estados pequenos).
"""
import csv
import io
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

import httpx

from app.sync.bcb_client import SeriesPoint

REQUEST_HEADERS = {
    "User-Agent": "IFB-Sync/1.0 (+https://github.com/douglasoliveira21/ifb2)",
}

RAZAO_MORTALIDADE_MATERNA_URL = "https://demas-dados-abertos.s3.amazonaws.com/csv/ripsa001mt.csv.zip"

# Códigos de UF do IBGE (os mesmos usados no CSV) -> sigla.
_IBGE_UF_CODE_TO_UF = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
    "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}


@dataclass(frozen=True)
class RipsaCsvSpec:
    url: str
    indicador: str  # coluna "Indicador" a filtrar, ex: "MRT.2.01"


RAZAO_MORTALIDADE_MATERNA_SPEC = RipsaCsvSpec(url=RAZAO_MORTALIDADE_MATERNA_URL, indicador="MRT.2.01")


def _download_rows(spec: RipsaCsvSpec, *, timeout: float) -> list[dict]:
    response = httpx.get(spec.url, headers=REQUEST_HEADERS, timeout=timeout, follow_redirects=True)
    response.raise_for_status()
    zf = zipfile.ZipFile(io.BytesIO(response.content))
    with zf.open(zf.namelist()[0]) as f:
        text = f.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return [row for row in reader if row.get("Indicador") == spec.indicador]


def fetch_razao_mortalidade_materna_by_state(
    spec: RipsaCsvSpec = RAZAO_MORTALIDADE_MATERNA_SPEC, *, timeout: float = 60.0
) -> dict[str, list[SeriesPoint]]:
    """Razão de mortalidade materna (óbitos maternos por 100 mil nascidos
    vivos), por estado — calculada a partir do numerador (óbitos
    corrigidos) e denominador (nascidos vivos) brutos do CSV."""
    rows = _download_rows(spec, timeout=timeout)

    by_state: dict[str, list[SeriesPoint]] = {}
    for row in rows:
        uf = _IBGE_UF_CODE_TO_UF.get(row["UF"])
        if uf is None:
            continue
        try:
            numerador = float(row["Numerador - Obitos maternos corrigido"])
            denominador = float(row["Denominador - Nascidos vivos"])
            fator = float(row["Fator"])
            year = int(row["Ano"])
        except (KeyError, ValueError):
            continue
        if denominador <= 0:
            continue
        value = (numerador / denominador) * fator
        by_state.setdefault(uf, []).append(SeriesPoint(reference_date=date(year, 12, 31), value=value))

    for points in by_state.values():
        points.sort(key=lambda p: p.reference_date)
    return by_state


def fetch_razao_mortalidade_materna_brasil(
    spec: RipsaCsvSpec = RAZAO_MORTALIDADE_MATERNA_SPEC, *, timeout: float = 60.0
) -> list[SeriesPoint]:
    """Mesma razão, agregada nacionalmente: soma dos óbitos corrigidos e
    dos nascidos vivos de todos os estados em cada ano, antes de
    calcular a razão — não a média das razões estaduais."""
    rows = _download_rows(spec, timeout=timeout)

    totals: dict[int, tuple[float, float, float]] = defaultdict(lambda: (0.0, 0.0, 100000.0))
    for row in rows:
        try:
            numerador = float(row["Numerador - Obitos maternos corrigido"])
            denominador = float(row["Denominador - Nascidos vivos"])
            fator = float(row["Fator"])
            year = int(row["Ano"])
        except (KeyError, ValueError):
            continue
        prev_num, prev_den, _ = totals[year]
        totals[year] = (prev_num + numerador, prev_den + denominador, fator)

    points = [
        SeriesPoint(reference_date=date(year, 12, 31), value=(num / den) * fator)
        for year, (num, den, fator) in totals.items()
        if den > 0
    ]
    points.sort(key=lambda p: p.reference_date)
    return points
