"""Cliente para os arquivos de Leitos SUS do Cadastro Nacional de
Estabelecimentos de Saúde (CNES) — Ministério da Saúde.

Diferente da API "DEMAS" (`apidadosabertos.saude.gov.br`), que se mostrou
instável em testes (filtro `uf` retorna 500 de forma consistente, e a
paginação por `offset` não termina de forma sensata — ver notas no
README), este módulo usa os arquivos CSV estáveis publicados no S3 do
Ministério da Saúde, um por ano, listados em
https://dadosabertos.saude.gov.br/dataset/hospitais-e-leitos — mesmo
padrão de "baixar arquivo, não depender de API ao vivo" já usado para o
IDEB (`inep_client.py`).

Cada arquivo anual traz uma linha por estabelecimento hospitalar por mês
de competência (`COMP`, formato `AAAAMM`) — o IFB usa sempre o último mês
disponível em cada arquivo (normalmente dezembro, mas arquivos do ano
corrente podem ter poucos meses publicados, dado o atraso normal do
CNES) e soma `LEITOS_SUS` por UF.

Validado contra dezembro/2023: total Brasil = 344.555 leitos SUS, SP
como maior estado (61.529), na mesma ordem de grandeza dos números de
leitos SUS amplamente divulgados pelo Ministério da Saúde/CNES.
"""
import csv
import functools
import io
import time
from collections import defaultdict
from datetime import date

import httpx

from app.sync.bcb_client import SeriesPoint

URL_TEMPLATE = "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/Leitos_SUS/Leitos_{year}.csv"

REQUEST_HEADERS = {
    "User-Agent": "IFB-Sync/1.0 (+https://github.com/douglasoliveira21/ifb2)",
}
MAX_ATTEMPTS = 3
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

FIRST_AVAILABLE_YEAR = 2015


@functools.lru_cache(maxsize=16)
def _download_year_csv(year: int, *, timeout: float) -> str | None:
    """Baixa o CSV de um ano. Retorna None se o ano ainda não foi
    publicado (403/404) — não é um erro, é a fonte não tendo esse ano
    ainda.

    Cacheado por processo: a sincronização Brasil e por estado leem o
    mesmo conjunto de arquivos anuais (dezenas de MB cada) — sem cache,
    cada uma baixaria tudo de novo."""
    url = URL_TEMPLATE.format(year=year)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = httpx.get(url, headers=REQUEST_HEADERS, timeout=timeout, follow_redirects=True)
        except httpx.TransportError:
            if attempt < MAX_ATTEMPTS:
                time.sleep(2 * attempt)
                continue
            raise
        if response.status_code in {403, 404}:
            return None
        if response.status_code in RETRY_STATUS_CODES and attempt < MAX_ATTEMPTS:
            time.sleep(2 * attempt)
            continue
        response.raise_for_status()
        return response.text
    raise AssertionError("unreachable")


def _sum_leitos_sus_by_state_last_month(csv_text: str) -> dict[str, int]:
    reader = csv.DictReader(io.StringIO(csv_text))
    latest_comp = ""
    rows: list[dict] = []
    for row in reader:
        rows.append(row)
        latest_comp = max(latest_comp, row["COMP"])

    totals: dict[str, int] = defaultdict(int)
    for row in rows:
        if row["COMP"] != latest_comp:
            continue
        raw = (row.get("LEITOS_SUS") or "").strip()
        totals[row["UF"]] += int(raw) if raw.isdigit() else 0

    return dict(totals)


def _fetch_totals_by_year(
    *, start_year: int, timeout: float
) -> dict[int, dict[str, int]]:
    """Baixa cada arquivo anual uma única vez e devolve {ano: {uf: total}}
    — usado tanto pela série por estado quanto pelo agregado Brasil, para
    não baixar os mesmos arquivos (dezenas de MB cada) duas vezes."""
    current_year = date.today().year
    totals_by_year: dict[int, dict[str, int]] = {}

    for year in range(start_year, current_year + 1):
        csv_text = _download_year_csv(year, timeout=timeout)
        if csv_text is None:
            continue
        totals_by_year[year] = _sum_leitos_sus_by_state_last_month(csv_text)

    return totals_by_year


def fetch_leitos_sus_by_state(
    *, start_year: int = FIRST_AVAILABLE_YEAR, timeout: float = 120.0
) -> dict[str, list[SeriesPoint]]:
    """Soma o total de leitos SUS por estado, um ponto por ano (o último
    mês disponível no arquivo daquele ano — normalmente dezembro).
    Arquivos ainda não publicados são simplesmente pulados."""
    by_state: dict[str, list[SeriesPoint]] = {}

    for year, totals in _fetch_totals_by_year(start_year=start_year, timeout=timeout).items():
        for uf, total in totals.items():
            by_state.setdefault(uf, []).append(SeriesPoint(reference_date=date(year, 1, 1), value=float(total)))

    for points in by_state.values():
        points.sort(key=lambda p: p.reference_date)

    return by_state


def fetch_leitos_sus_brasil(*, start_year: int = FIRST_AVAILABLE_YEAR, timeout: float = 120.0) -> list[SeriesPoint]:
    """Mesma leitura, agregada para o Brasil como um todo (soma de todos
    os estados em cada ano)."""
    points: list[SeriesPoint] = []
    for year, totals in _fetch_totals_by_year(start_year=start_year, timeout=timeout).items():
        points.append(SeriesPoint(reference_date=date(year, 1, 1), value=float(sum(totals.values()))))

    points.sort(key=lambda p: p.reference_date)
    return points
