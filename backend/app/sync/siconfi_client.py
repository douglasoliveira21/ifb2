"""Cliente para a API SICONFI (Tesouro Nacional) — usado tanto para o
Relatório de Gestão Fiscal (RGF: dívida consolidada líquida e despesa com
pessoal, ambos como % da Receita Corrente Líquida ajustada) quanto para o
Relatório Resumido da Execução Orçamentária (RREO: receita total
realizada), sempre por estado —
https://apidatalake.tesouro.gov.br/docs/siconfi/.

API pública sem autenticação. Os parâmetros de consulta (`id_ente`,
`in_periodicidade`, `co_tipo_demonstrativo`, `no_anexo`, `co_poder`) e os
nomes de `cod_conta`/`coluna` usados aqui foram confirmados empiricamente
contra a API real (não estão documentados de forma completa no portal),
consultando São Paulo (id_ente=35) em 2023: % da DCL sobre a RCL ajustada
= 127,92%, % da despesa com pessoal sobre a RCL ajustada = 42,33% e
receita total realizada = R$ 326,7 bilhões — os dois primeiros
consistentes com números de dívida estadual amplamente noticiados (SP tem
uma das maiores relações dívida/RCL do país, herdada da renegociação de
dívida com a União nos anos 1990), o terceiro na mesma ordem de grandeza
do orçamento estadual de SP amplamente divulgado.

`id_ente` para um estado é o código IBGE de 2 dígitos da UF (o mesmo
usado pelo SIDRA/IBGE, ver `IBGE_UF_CODES` em `ibge_client.py`) — não o
código de 7 dígitos usado para municípios.

**Sem dado antes de 2015**: a API não retorna nenhum registro para
exercícios anteriores a 2015, nem para RGF nem para RREO (testado de 2013
a 2014, sempre 0 resultados) — o SICONFI substituiu os sistemas antigos
do Tesouro (FINBRA/SISTN) nesse ano, e não há retroação de dados
anteriores.
"""
import time
from dataclasses import dataclass
from datetime import date

import httpx

from app.sync.bcb_client import SeriesPoint
from app.sync.ibge_client import IBGE_UF_CODES

RGF_URL = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/rgf"
RREO_URL = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/rreo"

REQUEST_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "IFB-Sync/1.0 (+https://github.com/douglasoliveira21/ifb2)",
}
MAX_ATTEMPTS = 3
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

FIRST_AVAILABLE_YEAR = 2015


@dataclass(frozen=True)
class RgfQuery:
    """Descreve qual conta e coluna ler dentro de um anexo do RGF.

    O Anexo 02 (dívida) traz 4 colunas por conta (saldo do exercício
    anterior + 3 quadrimestres); o IFB sempre lê o fechamento do 3º
    quadrimestre como o valor anual. O Anexo 01 (pessoal) traz só
    "Valor" e "% sobre a RCL Ajustada" para o quadrimestre consultado
    (aqui, sempre o 3º — fechamento do exercício)."""

    no_anexo: str  # "RGF-Anexo 01" (pessoal) ou "RGF-Anexo 02" (dívida)
    cod_conta: str
    column_marker: str


# A API do SICONFI tem um bug de codificação conhecido: acentos e símbolos
# em `coluna` chegam corrompidos ("Até o 3º Quadrimestre" vira algo
# ilegível), mesmo com Content-Type declarado como UTF-8. Os trechos
# puramente ASCII sobrevivem intactos, então o match usa só "o 3" +
# "Quadrimestre" em vez do texto completo da coluna.
DIVIDA_CONSOLIDADA_LIQUIDA_RCL = RgfQuery(
    no_anexo="RGF-Anexo 02", cod_conta="PercentualDaDCLSobreARCL", column_marker="o 3"
)
DESPESA_COM_PESSOAL_RCL = RgfQuery(
    no_anexo="RGF-Anexo 01", cod_conta="DespesaComPessoalTotal", column_marker="% sobre a RCL Ajustada"
)


@dataclass(frozen=True)
class RreoQuery:
    """Descreve qual conta e coluna ler dentro de um anexo do RREO. O
    Anexo 01 (Balanço Orçamentário) traz colunas de previsão e execução
    por bimestre; o IFB sempre lê "Até o Bimestre (c)" do 6º bimestre —
    o valor acumulado no ano inteiro (fechamento do exercício)."""

    no_anexo: str
    cod_conta: str


RECEITA_TOTAL_REALIZADA = RreoQuery(no_anexo="RREO-Anexo 01", cod_conta="TotalReceitas")


def _row_matches_column_rgf(query: RgfQuery, coluna: str) -> bool:
    if query.no_anexo == "RGF-Anexo 02":
        return query.column_marker in coluna and "Quadrimestre" in coluna
    return coluna == query.column_marker


def _row_matches_column_rreo(coluna: str) -> bool:
    # Mesmo bug de codificação do RGF (ver docstring do módulo) — "(c)" e
    # "Bimestre" sobrevivem intactos e distinguem "Até o Bimestre (c)"
    # (acumulado no ano) de "No Bimestre (b)" (só aquele bimestre).
    return "(c)" in coluna and "Bimestre" in coluna


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
        return response.json()["items"]
    raise AssertionError("unreachable")


def _fetch_rgf_state_year(query: RgfQuery, cod_ibge_uf: int, year: int, *, timeout: float) -> float | None:
    params = {
        "an_exercicio": year,
        "nr_periodo": 3,  # 3º quadrimestre = fechamento do exercício
        "id_ente": cod_ibge_uf,
        "in_periodicidade": "Q",
        "co_tipo_demonstrativo": "RGF",
        "no_anexo": query.no_anexo,
        "co_poder": "E",  # Poder Executivo estadual
    }
    rows = _get_with_retry(RGF_URL, params, timeout=timeout)
    for row in rows:
        if row.get("cod_conta") == query.cod_conta and _row_matches_column_rgf(query, row.get("coluna", "")):
            return float(row["valor"])
    return None


def fetch_rgf_by_state(
    query: RgfQuery, *, start_year: int = FIRST_AVAILABLE_YEAR, timeout: float = 30.0
) -> dict[str, list[SeriesPoint]]:
    """Busca um indicador do RGF (dívida ou despesa com pessoal, ambos
    como % da RCL ajustada) para os estados, um valor anual cada
    (fechamento do exercício). Estados/anos sem declaração publicada no
    SICONFI são simplesmente omitidos — nunca um valor inventado."""
    current_year = date.today().year
    by_state: dict[str, list[SeriesPoint]] = {}

    for cod_ibge_str, uf in IBGE_UF_CODES.items():
        cod_ibge = int(cod_ibge_str)
        points: list[SeriesPoint] = []
        for year in range(start_year, current_year + 1):
            value = _fetch_rgf_state_year(query, cod_ibge, year, timeout=timeout)
            if value is not None:
                points.append(SeriesPoint(reference_date=date(year, 1, 1), value=value))
        if points:
            by_state[uf] = points

    return by_state


def _fetch_rreo_state_year(query: RreoQuery, cod_ibge_uf: int, year: int, *, timeout: float) -> float | None:
    params = {
        "an_exercicio": year,
        "nr_periodo": 6,  # 6º bimestre = fechamento do exercício
        "id_ente": cod_ibge_uf,
        "co_tipo_demonstrativo": "RREO",
        "no_anexo": query.no_anexo,
    }
    rows = _get_with_retry(RREO_URL, params, timeout=timeout)
    for row in rows:
        if row.get("cod_conta") == query.cod_conta and _row_matches_column_rreo(row.get("coluna", "")):
            return float(row["valor"])
    return None


def fetch_rreo_by_state(
    query: RreoQuery = RECEITA_TOTAL_REALIZADA,
    *,
    start_year: int = FIRST_AVAILABLE_YEAR,
    timeout: float = 30.0,
) -> dict[str, list[SeriesPoint]]:
    """Busca um indicador do RREO (por padrão, receita total realizada)
    para os estados, um valor anual cada (acumulado até o 6º bimestre —
    fechamento do exercício). Mesmas regras do RGF: sem dado antes de
    2015, estados/anos sem declaração são omitidos."""
    current_year = date.today().year
    by_state: dict[str, list[SeriesPoint]] = {}

    for cod_ibge_str, uf in IBGE_UF_CODES.items():
        cod_ibge = int(cod_ibge_str)
        points: list[SeriesPoint] = []
        for year in range(start_year, current_year + 1):
            value = _fetch_rreo_state_year(query, cod_ibge, year, timeout=timeout)
            if value is not None:
                points.append(SeriesPoint(reference_date=date(year, 1, 1), value=value))
        if points:
            by_state[uf] = points

    return by_state
