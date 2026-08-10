"""Cliente para a API do SIDRA (Sistema IBGE de Recuperação Automática) —
https://apisidra.ibge.gov.br. Diferente do SGS/BCB, cada tabela do SIDRA
tem sua própria combinação de variável + classificações (sexo, idade
etc.), então a URL é montada dinamicamente por `app/sync/definitions.py`
via `SidraQuery`.

Os códigos de tabela/variável/classificação usados pelo IFB foram
confirmados manualmente, batendo os valores retornados contra números
oficiais amplamente divulgados — ver `app/sync/definitions.py`.
"""
import re
import time
from dataclasses import dataclass, field
from datetime import date

import httpx

from app.sync.bcb_client import SeriesPoint

BASE_URL = "https://apisidra.ibge.gov.br/values"

REQUEST_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "IFB-Sync/1.0 (+https://github.com/douglasoliveira21/ifb2)",
}
MAX_ATTEMPTS = 3
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

_YEAR_RE = re.compile(r"^(19|20)\d{2}$")
_NO_DATA_MARKERS = {"..", "...", "-", "X", None, ""}


@dataclass(frozen=True)
class SidraQuery:
    """Descreve uma consulta SIDRA: tabela, variável e classificações fixas
    (ex: sexo=Total, faixa etária=15 anos ou mais) — territ. sempre Brasil."""

    table: int
    variable: int
    # {codigo_classificacao: codigo_categoria} — categoria também aceita a
    # string "all" (todas as categorias), como no parâmetro da própria API.
    classifications: dict[int, int | str] = field(default_factory=dict)


def fetch_sidra_series(query: SidraQuery, *, timeout: float = 30.0) -> list[SeriesPoint]:
    """Busca uma série anual do SIDRA para o Brasil (nível territorial 1).
    Ignora linhas marcadas pelo IBGE como sem dado ('..', '-', 'X' etc.) —
    isso nunca deve virar um zero ou um valor inventado."""
    path_parts = [
        BASE_URL,
        f"t/{query.table}",
        "n1/1",
        f"v/{query.variable}",
        "p/all",
    ]
    for classification_code, category_code in query.classifications.items():
        path_parts.append(f"c{classification_code}/{category_code}")
    url = "/".join(path_parts)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        response = httpx.get(url, headers=REQUEST_HEADERS, timeout=timeout)
        if response.status_code in RETRY_STATUS_CODES and attempt < MAX_ATTEMPTS:
            time.sleep(2 * attempt)
            continue
        response.raise_for_status()
        rows = response.json()
        break

    points: list[SeriesPoint] = []
    for row in rows[1:]:  # primeira linha é o cabeçalho/legenda, não dado
        value_raw = row.get("V")
        if value_raw in _NO_DATA_MARKERS:
            continue
        year = _extract_year(row)
        if year is None:
            continue
        points.append(SeriesPoint(reference_date=date(year, 1, 1), value=float(value_raw)))

    points.sort(key=lambda p: p.reference_date)
    return points


def drop_future_years(points: list[SeriesPoint]) -> list[SeriesPoint]:
    """Algumas tabelas do IBGE (ex: projeção de população) publicam anos
    futuros junto com o histórico observado — o IFB nunca mostra um ano
    ainda não decorrido como se fosse dado real."""
    current_year = date.today().year
    return [p for p in points if p.reference_date.year <= current_year]


def _extract_year(row: dict) -> int | None:
    """Algumas tabelas (ex: projeções de população) têm mais de um campo
    'Ano' — um período de referência fixo (irrelevante aqui) e a
    classificação de ano que realmente varia linha a linha. A que importa
    sempre aparece por último na resposta do SIDRA, então pegamos a
    última ocorrência, não a primeira."""
    year: int | None = None
    for key, val in row.items():
        if key.endswith("N") and isinstance(val, str) and _YEAR_RE.fullmatch(val):
            year = int(val)
    return year
