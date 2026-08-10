"""Cliente para a API SGS (Sistema Gerenciador de Séries Temporais) do Banco
Central do Brasil — https://dadosabertos.bcb.gov.br/dataset/sgs.

Usada tanto para séries de propriedade do BCB (ex: Selic) quanto para séries
originadas em outras instituições e espelhadas pelo BCB (ex: IPCA/IBGE,
taxa de desocupação PNAD Contínua/IBGE). A atribuição de fonte de cada
indicador é definida em `app/sync/definitions.py`, não aqui.
"""
import time
from dataclasses import dataclass
from datetime import date, datetime

import httpx

BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"

REQUEST_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "IFB-Sync/1.0 (+https://github.com/douglasoliveira21/ifb2)",
}
MAX_ATTEMPTS = 3
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

# Confirmado com a própria API: séries de periodicidade DIÁRIA (ex: Selic,
# código 432) recusam com 406 qualquer consulta cuja janela (dataInicial→
# dataFinal, ou o histórico completo sem filtro) passe de 10 anos —
# "O sistema aceita uma janela de consulta de, no máximo, 10 anos em séries
# de periodicidade diária". Séries mensais não têm esse limite. Por isso
# `fetch_series` não serve para séries diárias muito longas — use
# `fetch_daily_series_chunked`.
DAILY_SERIES_MAX_WINDOW_YEARS = 10


@dataclass(frozen=True)
class SeriesPoint:
    reference_date: date
    value: float


def _get_with_retry(url: str, params: dict, *, timeout: float) -> list[dict]:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        response = httpx.get(url, params=params, headers=REQUEST_HEADERS, timeout=timeout)
        if response.status_code in RETRY_STATUS_CODES and attempt < MAX_ATTEMPTS:
            time.sleep(2 * attempt)
            continue
        response.raise_for_status()
        return response.json()
    raise AssertionError("unreachable")  # loop sempre retorna ou levanta


def _rows_to_points(rows: list[dict]) -> list[SeriesPoint]:
    return [
        SeriesPoint(
            reference_date=datetime.strptime(row["data"], "%d/%m/%Y").date(),
            value=float(row["valor"]),
        )
        for row in rows
    ]


def fetch_series(series_code: int, *, timeout: float = 30.0) -> list[SeriesPoint]:
    """Busca a série histórica completa. Só funciona para séries mensais (ou
    séries diárias curtas, <=10 anos) — a API do BCB recusa consultas sem
    filtro de data em séries diárias longas, ver `DAILY_SERIES_MAX_WINDOW_YEARS`.
    Levanta exceção em caso de falha — quem chama decide como registrar o
    erro (ver app/sync/run.py)."""
    url = BASE_URL.format(code=series_code)
    raw = _get_with_retry(url, {"formato": "json"}, timeout=timeout)
    return _rows_to_points(raw)


def fetch_daily_series_chunked(
    series_code: int, *, start_year: int = 2000, timeout: float = 30.0
) -> list[SeriesPoint]:
    """Busca uma série diária longa (ex: Selic) em blocos de até
    `DAILY_SERIES_MAX_WINDOW_YEARS` anos, respeitando o limite de janela de
    consulta da API do BCB para séries diárias, e concatena o resultado."""
    url = BASE_URL.format(code=series_code)
    current_year = date.today().year

    points: list[SeriesPoint] = []
    window_start = start_year
    while window_start <= current_year:
        window_end = min(window_start + DAILY_SERIES_MAX_WINDOW_YEARS - 1, current_year)
        params = {
            "formato": "json",
            "dataInicial": f"01/01/{window_start}",
            "dataFinal": f"31/12/{window_end}",
        }
        raw = _get_with_retry(url, params, timeout=timeout)
        points.extend(_rows_to_points(raw))
        window_start = window_end + 1

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
