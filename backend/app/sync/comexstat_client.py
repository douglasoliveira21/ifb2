"""Cliente para a API do Comex Stat (MDIC) — balança comercial brasileira
(exportações/importações), https://api-comexstat.mdic.gov.br.

Diferente das demais fontes do projeto, não há chave de acesso nem
autenticação — a API aceita POST com um corpo JSON descrevendo o filtro
(fluxo, período, quebras). Já é uma agregação pronta (o servidor soma os
valores), não microdados: uma única chamada com `details: ["state"]`
devolve o total por estado para todos os anos pedidos de uma vez.

**Rate limit agressivo e sem cabeçalho de sinalização**: a API devolve
HTTP 429 ("Você excedeu o limite de solicitações... tente novamente em
10 segundos") quando chamadas ficam muito próximas — na prática, mais
de uma chamada a cada ~10-15s já dispara o limite. `_post_with_retry`
trata 429 como uma condição de retry normal (não como erro fatal),
com espera progressiva.

Validado ao vivo contra números amplamente divulgados: exportações
totais de 2023 = US$ 339,7 bilhões (recorde histórico bastante
noticiado à época) e superávit comercial de 2023 (339,7 - 240,8 = US$
98,9 bilhões) bate com o superávit recorde de ~US$ 98,8 bilhões
amplamente reportado pela imprensa econômica no início de 2024. Por
estado, São Paulo lidera as exportações de 2024 com US$ 71,4 bilhões,
consistente com ser a maior economia exportadora do país.
"""
import time
from datetime import date

import httpx

from app.sync.bcb_client import SeriesPoint

BASE_URL = "https://api-comexstat.mdic.gov.br/general"

REQUEST_HEADERS = {
    "User-Agent": "IFB-Sync/1.0 (+https://github.com/douglasoliveira21/ifb2)",
    "Content-Type": "application/json",
}
MAX_ATTEMPTS = 6
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
RETRY_BASE_DELAY_SECONDS = 12

# Nome completo do estado (como devolvido pela API) -> sigla UF, conforme
# observado empiricamente na resposta com `details: ["state"]`. "Não
# Declarada" não é um estado (exportações sem UF de origem atribuída) —
# fica de fora do mapa de propósito, para nunca virar uma UF inventada.
STATE_NAME_TO_UF: dict[str, str] = {
    "Acre": "AC", "Alagoas": "AL", "Amapá": "AP", "Amazonas": "AM", "Bahia": "BA",
    "Ceará": "CE", "Distrito Federal": "DF", "Espírito Santo": "ES", "Goiás": "GO",
    "Maranhão": "MA", "Mato Grosso": "MT", "Mato Grosso do Sul": "MS",
    "Minas Gerais": "MG", "Paraná": "PR", "Paraíba": "PB", "Pará": "PA",
    "Pernambuco": "PE", "Piauí": "PI", "Rio Grande do Norte": "RN",
    "Rio Grande do Sul": "RS", "Rio de Janeiro": "RJ", "Rondônia": "RO",
    "Roraima": "RR", "Santa Catarina": "SC", "Sergipe": "SE", "São Paulo": "SP",
    "Tocantins": "TO",
}


def _post_with_retry(body: dict, *, timeout: float) -> dict:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = httpx.post(BASE_URL, headers=REQUEST_HEADERS, json=body, timeout=timeout)
        except httpx.TransportError:
            if attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_BASE_DELAY_SECONDS)
                continue
            raise
        if response.status_code in RETRY_STATUS_CODES and attempt < MAX_ATTEMPTS:
            time.sleep(RETRY_BASE_DELAY_SECONDS * attempt)
            continue
        response.raise_for_status()
        return response.json()
    raise AssertionError("unreachable")


def fetch_totals_brasil(flow: str, *, start_year: int, end_year: int, timeout: float = 30.0) -> list[SeriesPoint]:
    """Total anual (valor FOB, em dólares) de exportação ou importação —
    `flow` é "export" ou "import"."""
    body = {
        "flow": flow,
        "monthDetail": False,
        "period": {"from": f"{start_year}-01", "to": f"{end_year}-12"},
        "filters": [],
        "details": [],
        "metrics": ["metricFOB"],
    }
    data = _post_with_retry(body, timeout=timeout)
    points = [
        SeriesPoint(reference_date=date(int(row["year"]), 1, 1), value=float(row["metricFOB"]))
        for row in data["data"]["list"]
    ]
    points.sort(key=lambda p: p.reference_date)
    return points


def fetch_totals_by_state(
    flow: str, *, start_year: int, end_year: int, timeout: float = 30.0
) -> dict[str, list[SeriesPoint]]:
    """Mesmo total, quebrado por estado de origem/destino — uma única
    chamada cobre todos os anos e estados pedidos de uma vez."""
    body = {
        "flow": flow,
        "monthDetail": False,
        "period": {"from": f"{start_year}-01", "to": f"{end_year}-12"},
        "filters": [],
        "details": ["state"],
        "metrics": ["metricFOB"],
    }
    data = _post_with_retry(body, timeout=timeout)

    by_state: dict[str, list[SeriesPoint]] = {}
    for row in data["data"]["list"]:
        uf = STATE_NAME_TO_UF.get(row["state"])
        if uf is None:
            continue
        by_state.setdefault(uf, []).append(
            SeriesPoint(reference_date=date(int(row["year"]), 1, 1), value=float(row["metricFOB"]))
        )

    for points in by_state.values():
        points.sort(key=lambda p: p.reference_date)

    return by_state
