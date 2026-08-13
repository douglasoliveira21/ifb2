"""Cliente para a Taxa de Ocupação do Sistema Prisional — Levantamento
Nacional de Informações Penitenciárias (SISDEPEN), Secretaria Nacional
de Políticas Penais (Senappen/MJSP), publicado como CSV censitário (uma
linha por unidade prisional) em https://www.gov.br/senappen.

**Sem série histórica em arquivo único**: cada ciclo semestral é um CSV
separado (~1.700 colunas, uma linha por estabelecimento penal), sem um
arquivo consolidado com todos os ciclos disponível para download direto
— mesma limitação já documentada em `inep_taxa_rendimento_client.py`
para as Taxas de Rendimento do INEP. Por isso este cliente publica só o
ciclo mais recente; a URL abaixo precisa ser atualizada manualmente a
cada novo ciclo (semestral) publicado pela Senappen.

Conferido: 19º ciclo (2º semestre de 2025) — Brasil: capacidade
declarada 679.763 vagas, população prisional 936.981 pessoas, taxa de
ocupação 137,8%, mesma ordem de grandeza da superlotação já amplamente
noticiada para o sistema prisional brasileiro (historicamente entre
130% e 170% conforme os levantamentos Infopen/SISDEPEN).
"""
import csv
import io
from collections import defaultdict
from datetime import date

import httpx

from app.sync.bcb_client import SeriesPoint

REQUEST_HEADERS = {
    "User-Agent": "IFB-Sync/1.0 (+https://github.com/douglasoliveira21/ifb2)",
}

SISDEPEN_CSV_URL = (
    "https://www.gov.br/senappen/pt-br/servicos/sisdepen/bases-de-dados/2025/"
    "19o-ciclo-base-de-dados-2025-2-semestre.csv"
)
SISDEPEN_REFERENCE_DATE = date(2025, 12, 31)


def _resolve_columns(fieldnames: list[str]) -> dict[str, str]:
    capacidade_masc = next(f for f in fieldnames if f.endswith("Masculino | Total") and f.startswith("1.3 "))
    capacidade_fem = next(f for f in fieldnames if f.endswith("Feminino | Total") and f.startswith("1.3 "))
    populacao_total = next(
        f
        for f in fieldnames
        if f.startswith("5.1 Quantidade de pessoas privadas de liberdade")
        and len(f.split(" | ")) == 2
        and f.split(" | ")[-1].strip() == "Total"
    )
    return {"uf": "UF", "capacidade_masc": capacidade_masc, "capacidade_fem": capacidade_fem, "populacao": populacao_total}


def _parse_number(raw: str) -> float:
    raw = (raw or "").strip().replace(",", ".")
    return float(raw) if raw else 0.0


def _aggregate_by_state(url: str, *, timeout: float) -> dict[str, tuple[float, float]]:
    """Retorna {uf: (populacao_total, capacidade_total)}."""
    response = httpx.get(url, headers=REQUEST_HEADERS, timeout=timeout, follow_redirects=True)
    response.raise_for_status()
    reader = csv.DictReader(io.StringIO(response.content.decode("utf-8")), delimiter=";")
    cols = _resolve_columns(reader.fieldnames or [])

    totals: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
    for row in reader:
        uf = (row.get(cols["uf"]) or "").strip()
        if not uf:
            continue
        populacao = _parse_number(row.get(cols["populacao"], ""))
        capacidade = _parse_number(row.get(cols["capacidade_masc"], "")) + _parse_number(
            row.get(cols["capacidade_fem"], "")
        )
        totals[uf][0] += populacao
        totals[uf][1] += capacidade

    return {uf: (pop, cap) for uf, (pop, cap) in totals.items()}


def fetch_taxa_ocupacao_prisional_by_state(
    url: str = SISDEPEN_CSV_URL, *, timeout: float = 120.0
) -> dict[str, list[SeriesPoint]]:
    totals = _aggregate_by_state(url, timeout=timeout)
    return {
        uf: [SeriesPoint(reference_date=SISDEPEN_REFERENCE_DATE, value=round(pop / cap * 100, 1))]
        for uf, (pop, cap) in totals.items()
        if cap > 0
    }


def fetch_taxa_ocupacao_prisional_brasil(url: str = SISDEPEN_CSV_URL, *, timeout: float = 120.0) -> list[SeriesPoint]:
    totals = _aggregate_by_state(url, timeout=timeout)
    pop_total = sum(pop for pop, _cap in totals.values())
    cap_total = sum(cap for _pop, cap in totals.values())
    if cap_total <= 0:
        return []
    return [SeriesPoint(reference_date=SISDEPEN_REFERENCE_DATE, value=round(pop_total / cap_total * 100, 1))]
