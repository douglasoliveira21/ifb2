"""Cliente para a API Pública do DataJud (CNJ) — https://api-publica.datajud.cnj.jus.br.

Diferente das demais fontes do projeto, esta API não devolve uma série
pronta: é uma API de busca Elasticsearch, uma coleção por tribunal (27
tribunais de justiça estaduais + DF), cada uma com dezenas de milhões de
processos. O IFB não baixa os processos — faz uma consulta de contagem
(`size: 0`, `track_total_hits`) filtrada por ano de ajuizamento
(`dataAjuizamento`, string no formato AAAAMMDDHHMMSS, comparável como
range de texto porque é de largura fixa), uma por estado por ano, e soma
para o total Brasil.

A chave usada abaixo é a "chave pública" documentada oficialmente pelo
próprio CNJ para uso livre por qualquer aplicação — não é um segredo do
IFB, está publicada em texto claro no wiki oficial:
https://datajud-wiki.cnj.jus.br/api-publica/acesso/
O CNJ avisa que pode trocar essa chave a qualquer momento por segurança;
se isso acontecer, o sync passa a falhar com 401 até a chave ser
atualizada aqui.

Validado contra números plausíveis: TJSP (maior tribunal estadual do
país) registrou 3.329.580 processos ajuizados em 2024, TJRS 1.473.514,
TJMA 565.250, TJDFT 39.930 — ordem de grandeza compatível com o tamanho
de cada tribunal.
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

import httpx

from app.sync.bcb_client import SeriesPoint

BASE_URL = "https://api-publica.datajud.cnj.jus.br"

# Chave pública documentada pelo CNJ — ver docstring do módulo.
API_KEY_HEADER = {
    "Authorization": "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw==",
    "Content-Type": "application/json",
}

MAX_ATTEMPTS = 3
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

# Alias do índice do Tribunal de Justiça de cada UF, conforme
# https://datajud-wiki.cnj.jus.br/api-publica/endpoints/ — todos os 27
# tribunais de justiça estaduais seguem "tj" + sigla minúscula, exceto o
# Distrito Federal, que é "tjdft" (Tribunal de Justiça do Distrito
# Federal e dos Territórios), não "tjdf".
STATE_TJ_ALIAS: dict[str, str] = {
    "AC": "tjac", "AL": "tjal", "AM": "tjam", "AP": "tjap", "BA": "tjba",
    "CE": "tjce", "DF": "tjdft", "ES": "tjes", "GO": "tjgo", "MA": "tjma",
    "MG": "tjmg", "MS": "tjms", "MT": "tjmt", "PA": "tjpa", "PB": "tjpb",
    "PE": "tjpe", "PI": "tjpi", "PR": "tjpr", "RJ": "tjrj", "RN": "tjrn",
    "RO": "tjro", "RR": "tjrr", "RS": "tjrs", "SC": "tjsc", "SE": "tjse",
    "SP": "tjsp", "TO": "tjto",
}


def _count_processos_ajuizados(alias: str, year: int, *, timeout: float) -> int:
    """Conta processos com `dataAjuizamento` dentro do ano informado, via
    agregação de contagem (`size: 0`) — nunca baixa os processos em si."""
    body = {
        "size": 0,
        "track_total_hits": True,
        "query": {
            "range": {
                "dataAjuizamento": {
                    "gte": f"{year}0101000000",
                    "lt": f"{year + 1}0101000000",
                }
            }
        },
    }
    url = f"{BASE_URL}/api_publica_{alias}/_search"
    last_exc: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = httpx.post(url, headers=API_KEY_HEADER, json=body, timeout=timeout)
        except httpx.TransportError as exc:
            last_exc = exc
            if attempt < MAX_ATTEMPTS:
                time.sleep(2 * attempt)
                continue
            raise
        if response.status_code in RETRY_STATUS_CODES and attempt < MAX_ATTEMPTS:
            time.sleep(2 * attempt)
            continue
        response.raise_for_status()
        return response.json()["hits"]["total"]["value"]
    raise last_exc if last_exc else AssertionError("unreachable")


def fetch_processos_ajuizados_by_state(
    year: int, *, max_workers: int = 10, timeout: float = 60.0
) -> dict[str, int]:
    """Total de processos ajuizados no ano em cada Tribunal de Justiça
    estadual — uma consulta de contagem por estado, em paralelo (mesmo
    padrão de `siconfi_client.fetch_rgf_by_municipio`)."""
    results: dict[str, int] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_count_processos_ajuizados, alias, year, timeout=timeout): uf
            for uf, alias in STATE_TJ_ALIAS.items()
        }
        for future in as_completed(futures):
            uf = futures[future]
            results[uf] = future.result()
    return results


def fetch_processos_ajuizados_series_by_state(
    *, start_year: int, end_year: int, max_workers: int = 10, timeout: float = 60.0
) -> dict[str, list[SeriesPoint]]:
    """Série anual de processos ajuizados por estado, de `start_year` até
    `end_year` (inclusive)."""
    by_state: dict[str, list[SeriesPoint]] = {uf: [] for uf in STATE_TJ_ALIAS}
    for year in range(start_year, end_year + 1):
        counts = fetch_processos_ajuizados_by_state(year, max_workers=max_workers, timeout=timeout)
        for uf, count in counts.items():
            by_state[uf].append(SeriesPoint(reference_date=date(year, 1, 1), value=float(count)))
    return by_state


def fetch_processos_ajuizados_series_brasil(
    *, start_year: int, end_year: int, max_workers: int = 10, timeout: float = 60.0
) -> list[SeriesPoint]:
    """Mesma série, somada para o Brasil (soma dos 27 tribunais de justiça
    estaduais — não inclui Justiça Federal, do Trabalho, Eleitoral nem
    Superiores/STJ/STF, que têm índices próprios não cobertos aqui)."""
    by_state = fetch_processos_ajuizados_series_by_state(
        start_year=start_year, end_year=end_year, max_workers=max_workers, timeout=timeout
    )
    totals_by_year: dict[int, float] = {}
    for points in by_state.values():
        for point in points:
            totals_by_year[point.reference_date.year] = (
                totals_by_year.get(point.reference_date.year, 0.0) + point.value
            )
    return sorted(
        (SeriesPoint(reference_date=date(year, 1, 1), value=total) for year, total in totals_by_year.items()),
        key=lambda p: p.reference_date,
    )
