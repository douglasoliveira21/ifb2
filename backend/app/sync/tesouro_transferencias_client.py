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
from datetime import date

import httpx

from app.sync.bcb_client import SeriesPoint

BASE_URL = "https://apiapex.tesouro.gov.br/aria/v1/transferencias_constitucionais/custom/por_estados"

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


def _get_with_retry(params: dict, *, timeout: float) -> list[dict]:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = httpx.get(BASE_URL, params=params, headers=REQUEST_HEADERS, timeout=timeout)
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
    rows = _get_with_retry(params, timeout=timeout)

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
