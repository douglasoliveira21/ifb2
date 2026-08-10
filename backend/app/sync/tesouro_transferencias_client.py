"""Cliente para a API de Transferências Constitucionais do Tesouro Nacional
— repasses da União a estados via FPE, FUNDEB, royalties (ANP, ITAIPU,
CFH, CFEM...), IPI-Exportação, Lei Kandir, CIDE-Combustíveis, IOF-Ouro e
demais transferências obrigatórias listadas pelo Tesouro.

A API não tem documentação pública indexada por buscador — a URL real
(`https://apiapex.tesouro.gov.br/aria/`) e os parâmetros de consulta só
aparecem depois de carregar a página de visualização do APEX
(`sisweb.tesouro.gov.br/apex/f?p=10250:7:...`) em um browser e capturar a
chamada de rede que busca a especificação OpenAPI embutida — ela mesma
avisa "Para solicitar acesso, entrar em contato com
desenvolvimento@tesouro.gov.br", mas na prática responde sem qualquer
autenticação. Confirmado empiricamente que os 27 estados e todos os anos
podem ser buscados em uma única requisição, retornando ~23 mil linhas
(uma por estado × ano × mês × tipo de transferência).

Cobertura por transferência começa em anos diferentes (a mais antiga,
FPE/FPM, desde 1997) — ver o campo `transferencia` de cada linha. O IFB
soma todas as modalidades por estado e ano, sem tentar decompor por tipo
nesta primeira integração.
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

import httpx

from app.sync.bcb_client import SeriesPoint

BASE_URL = "https://apiapex.tesouro.gov.br/aria/v1/transferencias_constitucionais/custom/por_estados"
MUNICIPIO_URL = "https://apiapex.tesouro.gov.br/aria/v1/transferencias_constitucionais/custom/por_estado_municipio"

REQUEST_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "IFB-Sync/1.0 (+https://github.com/douglasoliveira21/ifb2)",
}
MAX_ATTEMPTS = 3
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

# API do Tesouro para transferências constitucionais confirmada em produção
# desde 1997 (FPE/FPM) — o IFB usa 2015 como início por consistência com as
# demais séries estaduais de contas públicas (SICONFI), todas limitadas a
# esse período.
FIRST_AVAILABLE_YEAR = 2015

# Todos os 27 códigos internos de estado usados por esta API (1 a 27, sem
# lacunas — não são os códigos IBGE) — confirmados via
# `/custom/estados`. O `uf` de cada linha da resposta já vem como sigla,
# então esses códigos só servem para parametrizar a busca, nunca para
# agrupar o resultado.
_TESOURO_ESTADO_CODES = range(1, 28)


def _get_with_retry(url: str, params: dict, *, timeout: float) -> list[dict]:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = httpx.get(url, params=params, headers=REQUEST_HEADERS, timeout=timeout)
        except httpx.TransportError:
            if attempt < MAX_ATTEMPTS:
                time.sleep(2 * attempt)
                continue
            raise
        if response.status_code in RETRY_STATUS_CODES and attempt < MAX_ATTEMPTS:
            time.sleep(2 * attempt)
            continue
        response.raise_for_status()
        return response.json()["registros"]
    raise AssertionError("unreachable")


def fetch_transferencias_constitucionais_by_state(
    *, start_year: int = FIRST_AVAILABLE_YEAR, timeout: float = 60.0
) -> dict[str, list[SeriesPoint]]:
    """Busca, em uma única requisição, todas as transferências
    constitucionais para os 27 estados e soma por (UF, ano). Anos sem
    nenhum repasse registrado não geram ponto."""
    current_year = date.today().year
    params = {
        "p_estado": ":".join(str(code) for code in _TESOURO_ESTADO_CODES),
        "p_ano": ":".join(str(year) for year in range(start_year, current_year + 1)),
    }
    rows = _get_with_retry(BASE_URL, params, timeout=timeout)

    totals: dict[tuple[str, int], float] = {}
    for row in rows:
        key = (row["uf"], int(row["ano"]))
        totals[key] = totals.get(key, 0.0) + float(row["valor"])

    by_state: dict[str, list[SeriesPoint]] = {}
    for (uf, year), total in totals.items():
        by_state.setdefault(uf, []).append(SeriesPoint(reference_date=date(year, 1, 1), value=total))

    for points in by_state.values():
        points.sort(key=lambda p: p.reference_date)

    return by_state


def _fetch_municipio_rows_for_state(tesouro_estado_code: int, year: int, *, timeout: float) -> list[dict]:
    params = {"p_estado": tesouro_estado_code, "p_ano": year, "pageSize": 100000}
    return _get_with_retry(MUNICIPIO_URL, params, timeout=timeout)


def fetch_transferencias_constitucionais_by_municipio(
    *, year: int | None = None, timeout: float = 120.0, max_workers: int = 8
) -> dict[str, list[SeriesPoint]]:
    """Soma as transferências constitucionais por município, para um único
    ano (por padrão o último ano completo — o atual menos 1).

    **Só um ano, não histórico completo**: diferente da série por estado
    (que traz todos os anos numa única resposta pequena), a granularidade
    municipal multiplica o volume por ~206x (5.570 municípios vs 27
    estados) — buscar o histórico completo (2015 a hoje) somaria dezenas
    de milhões de linhas. Confirmado empiricamente: só São Paulo/2023 já
    retorna ~40 mil linhas (645 municípios × 12 meses × ~5 modalidades).
    Um ano é suficiente para o objetivo do piloto (mostrar o repasse mais
    recente por município) sem tornar o sync inviável.

    As 27 requisições (uma por estado) são feitas em paralelo — a escrita
    no banco continua sequencial, feita por `sync_by_municipio` em
    `app/sync/run.py`; só a busca HTTP é concorrente aqui."""
    target_year = year if year is not None else date.today().year - 1

    totals: dict[str, float] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_fetch_municipio_rows_for_state, code, target_year, timeout=timeout): code
            for code in _TESOURO_ESTADO_CODES
        }
        for future in as_completed(futures):
            rows = future.result()
            for row in rows:
                codigo_ibge = str(row["CO_IBGE"])
                totals[codigo_ibge] = totals.get(codigo_ibge, 0.0) + float(row["VALOR"])

    return {
        codigo_ibge: [SeriesPoint(reference_date=date(target_year, 1, 1), value=total)]
        for codigo_ibge, total in totals.items()
    }
