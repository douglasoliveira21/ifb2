from datetime import date

import httpx
import pytest

from app.sync.bcb_client import SeriesPoint
from app.sync.ibge_client import SidraQuery, drop_future_years, fetch_municipio_codes, fetch_sidra_series

SIMPLE_PAYLOAD = [
    {"NC": "Nível Territorial (Código)"},  # linha de cabeçalho, deve ser ignorada
    {"NC": "1", "D1N": "Brasil", "D2N": "Taxa", "D3N": "2022", "V": "5.6"},
    {"NC": "1", "D1N": "Brasil", "D2N": "Taxa", "D3N": "2023", "V": "5.4"},
    {"NC": "1", "D1N": "Brasil", "D2N": "Taxa", "D3N": "2021", "V": ".."},  # sem dado
]


def test_fetch_sidra_series_parses_and_skips_no_data(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, headers: dict, timeout: float) -> httpx.Response:
        return httpx.Response(200, json=SIMPLE_PAYLOAD, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    points = fetch_sidra_series(SidraQuery(table=7113, variable=10267, classifications={2: 6794, 58: 2795}))

    assert points == [
        SeriesPoint(reference_date=date(2022, 1, 1), value=5.6),
        SeriesPoint(reference_date=date(2023, 1, 1), value=5.4),
    ]


def test_fetch_sidra_series_uses_last_year_like_field(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tabelas de projeção (ex: 7362) têm um campo 'Ano' fixo/irrelevante e
    outro que varia de verdade — o que vale é sempre o último encontrado."""
    payload = [
        {"NC": "cabecalho"},
        {"D3N": "2018", "D5N": "2001", "V": "70.28"},
    ]

    def fake_get(url: str, headers: dict, timeout: float) -> httpx.Response:
        return httpx.Response(200, json=payload, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    points = fetch_sidra_series(SidraQuery(table=7362, variable=2503, classifications={2: 6794, 1933: "all"}))

    assert points == [SeriesPoint(reference_date=date(2001, 1, 1), value=70.28)]


def test_drop_future_years_keeps_only_past_and_current() -> None:
    points = [
        SeriesPoint(reference_date=date(2020, 1, 1), value=1.0),
        SeriesPoint(reference_date=date(2100, 1, 1), value=2.0),
    ]

    filtered = drop_future_years(points)

    assert filtered == [SeriesPoint(reference_date=date(2020, 1, 1), value=1.0)]


def test_fetch_municipio_codes_returns_string_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = [
        {"id": 3550308, "nome": "São Paulo"},
        {"id": 3509502, "nome": "Campinas"},
    ]

    def fake_get(url: str, headers: dict, timeout: float) -> httpx.Response:
        return httpx.Response(200, json=payload, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    codes = fetch_municipio_codes()

    assert codes == ["3550308", "3509502"]
