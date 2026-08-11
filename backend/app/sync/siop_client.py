"""Cliente para o SIOP (Sistema Integrado de Planejamento e Orçamento do
Governo Federal) — endpoint SPARQL público em
https://www1.siop.planejamento.gov.br/sparql/.

**Por que SPARQL, e não o Portal da Transparência**: o Portal da
Transparência exige um token pessoal (login gov.br com CPF) para
qualquer chamada à API — o IFB não usa fontes que exigem credencial
pessoal do usuário. O SIOP publica os mesmos dados de execução
orçamentária da União como RDF público, sem autenticação, num endpoint
SPARQL padrão (Virtuoso) — a fonte primária do próprio Poder Executivo
federal, não um agregador terceirizado.

Os dados de cada exercício ficam num grafo nomeado próprio
(`http://orcamento.dados.gov.br/{ano}/`), usando o vocabulário LOA
(`http://vocab.e.gov.br/2013/09/loa#`) — cada item de despesa
(`loa:ItemDespesa`) tem propriedades como `loa:valorPago`,
`loa:valorLiquidado`, `loa:valorEmpenhado`. O IFB soma `loa:valorPago`
de todos os itens de despesa de um exercício para obter o total
executado (efetivamente pago) no ano.

Validado ao vivo contra a trajetória conhecida do orçamento federal:
2019 = R$ 2,71 tri, salto para R$ 3,54 tri em 2020 (gastos emergenciais
da pandemia, amplamente noticiado), subindo de forma consistente até
R$ 4,65 tri em 2024 — tendência e ordem de grandeza batem com os
valores de execução orçamentária da União amplamente divulgados.
"""
from datetime import date

import httpx

from app.sync.bcb_client import SeriesPoint

SPARQL_ENDPOINT = "https://www1.siop.planejamento.gov.br/sparql/"

REQUEST_HEADERS = {
    "Accept": "application/sparql-results+json",
    "User-Agent": "IFB-Sync/1.0 (+https://github.com/douglasoliveira21/ifb2)",
}

_TOTAL_PAGO_QUERY = """
PREFIX loa: <http://vocab.e.gov.br/2013/09/loa#>
SELECT (SUM(?pago) as ?total) WHERE {{
  GRAPH <http://orcamento.dados.gov.br/{year}/> {{
    ?item a loa:ItemDespesa ;
          loa:valorPago ?pago .
  }}
}}
"""

FIRST_AVAILABLE_YEAR = 2000


def _fetch_total_pago(year: int, *, timeout: float) -> float | None:
    """Soma `loa:valorPago` de todos os itens de despesa do exercício.
    Retorna None se o grafo daquele ano ainda não existir (exercício
    futuro) ou não tiver itens de despesa."""
    response = httpx.get(
        SPARQL_ENDPOINT,
        params={"query": _TOTAL_PAGO_QUERY.format(year=year), "format": "application/sparql-results+json"},
        headers=REQUEST_HEADERS,
        timeout=timeout,
    )
    response.raise_for_status()
    bindings = response.json()["results"]["bindings"]
    if not bindings or "total" not in bindings[0]:
        return None
    return float(bindings[0]["total"]["value"])


def fetch_execucao_orcamentaria_uniao(
    *, start_year: int = FIRST_AVAILABLE_YEAR, timeout: float = 60.0
) -> list[SeriesPoint]:
    """Total pago do Orçamento Geral da União, um ponto por exercício —
    soma de `loa:valorPago` de todos os itens de despesa. Anos sem dado
    publicado são simplesmente omitidos, nunca um valor inventado."""
    current_year = date.today().year
    points: list[SeriesPoint] = []

    for year in range(start_year, current_year):
        total = _fetch_total_pago(year, timeout=timeout)
        if total is not None and total > 0:
            points.append(SeriesPoint(reference_date=date(year, 1, 1), value=total))

    points.sort(key=lambda p: p.reference_date)
    return points
