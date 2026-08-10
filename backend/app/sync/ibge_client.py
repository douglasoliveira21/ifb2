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
MUNICIPIOS_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

REQUEST_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "IFB-Sync/1.0 (+https://github.com/douglasoliveira21/ifb2)",
}
MAX_ATTEMPTS = 3
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

_YEAR_RE = re.compile(r"^(19|20)\d{2}$")
_NO_DATA_MARKERS = {"..", "...", "-", "X", None, ""}

# Códigos numéricos de UF do IBGE -> sigla, conforme retornados no campo
# D1C/D1N das respostas do SIDRA quando a consulta é feita em nível n3.
IBGE_UF_CODES: dict[str, str] = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA",
    "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS",
    "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}


@dataclass(frozen=True)
class SidraQuery:
    """Descreve uma consulta SIDRA: tabela, variável e classificações fixas
    (ex: sexo=Total, faixa etária=15 anos ou mais)."""

    table: int
    variable: int
    # {codigo_classificacao: codigo_categoria} — categoria também aceita a
    # string "all" (todas as categorias), como no parâmetro da própria API.
    classifications: dict[int, int | str] = field(default_factory=dict)


def _build_url(query: SidraQuery, territorial_level: str, territorial_code: str) -> str:
    path_parts = [
        BASE_URL,
        f"t/{query.table}",
        f"{territorial_level}/{territorial_code}",
        f"v/{query.variable}",
        "p/all",
    ]
    for classification_code, category_code in query.classifications.items():
        path_parts.append(f"c{classification_code}/{category_code}")
    return "/".join(path_parts)


def _get_rows(url: str, *, timeout: float) -> list[dict]:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        response = httpx.get(url, headers=REQUEST_HEADERS, timeout=timeout)
        if response.status_code in RETRY_STATUS_CODES and attempt < MAX_ATTEMPTS:
            time.sleep(2 * attempt)
            continue
        response.raise_for_status()
        return response.json()[1:]  # primeira linha é o cabeçalho/legenda, não dado
    raise AssertionError("unreachable")


def fetch_sidra_series(query: SidraQuery, *, timeout: float = 30.0) -> list[SeriesPoint]:
    """Busca uma série anual do SIDRA para o Brasil (nível territorial 1).
    Ignora linhas marcadas pelo IBGE como sem dado ('..', '-', 'X' etc.) —
    isso nunca deve virar um zero ou um valor inventado."""
    rows = _get_rows(_build_url(query, "n1", "1"), timeout=timeout)
    return _rows_to_points(rows)


def fetch_sidra_series_by_state(query: SidraQuery, *, timeout: float = 30.0) -> dict[str, list[SeriesPoint]]:
    """Busca a mesma série por UF (nível territorial 3, todos os estados de
    uma vez). Retorna um dict sigla -> série; estados sem código IBGE
    reconhecido são ignorados (não deveria acontecer, é uma checagem de
    segurança)."""
    rows = _get_rows(_build_url(query, "n3", "all"), timeout=timeout)

    by_state: dict[str, list[dict]] = {}
    for row in rows:
        uf = IBGE_UF_CODES.get(row.get("D1C", ""))
        if uf is None:
            continue
        by_state.setdefault(uf, []).append(row)

    return {uf: _rows_to_points(state_rows) for uf, state_rows in by_state.items()}


def _rows_to_points(rows: list[dict]) -> list[SeriesPoint]:
    points: list[SeriesPoint] = []
    for row in rows:
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


def drop_future_years_by_state(by_state: dict[str, list[SeriesPoint]]) -> dict[str, list[SeriesPoint]]:
    return {uf: drop_future_years(points) for uf, points in by_state.items()}


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


def fetch_municipio_codes(*, timeout: float = 60.0) -> list[str]:
    """Lista os ~5.570 códigos IBGE de município (7 dígitos, string) via a
    API de Localidades do IBGE — não é a API do SIDRA usada no resto deste
    módulo, mas é do mesmo órgão. Fonte compartilhada por
    `seed_municipios.py` e pelos conectores municipais (SICONFI, Tesouro)
    que precisam enumerar municípios um por um."""
    response = httpx.get(MUNICIPIOS_URL, headers=REQUEST_HEADERS, timeout=timeout)
    response.raise_for_status()
    return [str(item["id"]) for item in response.json()]
