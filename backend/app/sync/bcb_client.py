"""Cliente para a API SGS (Sistema Gerenciador de Séries Temporais) do Banco
Central do Brasil — https://dadosabertos.bcb.gov.br/dataset/sgs.

Usada tanto para séries de propriedade do BCB (ex: Selic) quanto para séries
originadas em outras instituições e espelhadas pelo BCB (ex: IPCA/IBGE,
taxa de desocupação PNAD Contínua/IBGE). A atribuição de fonte de cada
indicador é definida em `app/sync/definitions.py`, não aqui.
"""
from dataclasses import dataclass
from datetime import date, datetime

import httpx

BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"


@dataclass(frozen=True)
class SeriesPoint:
    reference_date: date
    value: float


def fetch_series(series_code: int, *, timeout: float = 30.0) -> list[SeriesPoint]:
    """Busca a série histórica completa. Levanta exceção em caso de falha —
    quem chama decide como registrar o erro (ver app/sync/run.py)."""
    url = BASE_URL.format(code=series_code)
    response = httpx.get(url, params={"formato": "json"}, timeout=timeout)
    response.raise_for_status()
    raw = response.json()

    points: list[SeriesPoint] = []
    for row in raw:
        reference_date = datetime.strptime(row["data"], "%d/%m/%Y").date()
        points.append(SeriesPoint(reference_date=reference_date, value=float(row["valor"])))
    return points


def resample_to_month_end(points: list[SeriesPoint]) -> list[SeriesPoint]:
    """Reduz uma série diária a um ponto por mês (o último disponível no mês),
    normalizando a data para o dia 1 — mesma convenção usada pelas séries
    já mensais do BCB/IBGE, para manter os indicadores comparáveis."""
    by_month: dict[tuple[int, int], SeriesPoint] = {}
    for point in sorted(points, key=lambda p: p.reference_date):
        key = (point.reference_date.year, point.reference_date.month)
        by_month[key] = point

    return [
        SeriesPoint(reference_date=date(year, month, 1), value=point.value)
        for (year, month), point in sorted(by_month.items())
    ]


def invert_sign(points: list[SeriesPoint]) -> list[SeriesPoint]:
    """Inverte o sinal de uma série — usado quando a fonte publica o dado na
    convenção oposta à que o IFB expõe (ex: NFSP do BCB é positiva quando há
    déficit; o IFB expõe "resultado primário" com a convenção usual, positivo
    = superávit). É uma transformação de unidade documentada na metodologia
    do indicador, não uma alteração do valor em si."""
    return [SeriesPoint(reference_date=p.reference_date, value=-p.value) for p in points]
