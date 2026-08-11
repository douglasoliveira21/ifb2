from datetime import date

import httpx
import pytest

from app.sync.bcb_client import SeriesPoint
from app.sync.siop_client import fetch_execucao_orcamentaria_uniao

CURRENT_YEAR = date.today().year


def _sparql_response(total: float | None) -> dict:
    bindings = [{"total": {"type": "typed-literal", "value": str(total)}}] if total is not None else []
    return {"head": {"vars": ["total"]}, "results": {"bindings": bindings}}


def test_fetch_execucao_orcamentaria_uniao_parses_years_with_data(monkeypatch: pytest.MonkeyPatch) -> None:
    totals = {2023: 4_364_787_995_299.02, 2024: 4_647_521_944_093.30}

    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        query = params["query"]
        for year, total in totals.items():
            if f"/{year}/" in query:
                return httpx.Response(200, json=_sparql_response(total), request=httpx.Request("GET", url))
        return httpx.Response(200, json=_sparql_response(None), request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    points = fetch_execucao_orcamentaria_uniao(start_year=2023)

    assert points == [
        SeriesPoint(reference_date=date(2023, 1, 1), value=4_364_787_995_299.02),
        SeriesPoint(reference_date=date(2024, 1, 1), value=4_647_521_944_093.30),
    ]


def test_fetch_execucao_orcamentaria_uniao_skips_years_without_graph(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        return httpx.Response(200, json=_sparql_response(None), request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    assert fetch_execucao_orcamentaria_uniao(start_year=CURRENT_YEAR - 2) == []
