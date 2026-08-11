from datetime import date

import httpx
import pytest

from app.sync.bcb_client import SeriesPoint
from app.sync.deter_client import fetch_area_desmatada_brasil, fetch_area_desmatada_by_state

CURRENT_YEAR = date.today().year


def _feature(uf: str, year_2digit: str, month: str, area: float, cl: str = "alerta") -> dict:
    return {
        "type": "Feature",
        "geometry": None,
        "properties": {"cl": cl, "ar": area, "y": year_2digit, "m": month, "uf": uf, "np": 10},
    }


def _response(features: list[dict]) -> dict:
    return {"type": "FeatureCollection", "features": features}


def test_fetch_area_desmatada_by_state_sums_months_into_years(monkeypatch: pytest.MonkeyPatch) -> None:
    features = [
        _feature("BA", "24", "01", 100.0),
        _feature("BA", "24", "02", 50.0),
        _feature("GO", "24", "01", 20.0),
        _feature("BA", "23", "12", 10.0),
    ]

    def fake_get(url: str, headers: dict, timeout: float) -> httpx.Response:
        return httpx.Response(200, json=_response(features), request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    by_state = fetch_area_desmatada_by_state()

    assert by_state["BA"] == [
        SeriesPoint(reference_date=date(2023, 1, 1), value=10.0),
        SeriesPoint(reference_date=date(2024, 1, 1), value=150.0),
    ]
    assert by_state["GO"] == [SeriesPoint(reference_date=date(2024, 1, 1), value=20.0)]


def test_fetch_area_desmatada_ignores_non_alerta_class_and_current_year(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_year_2digit = f"{CURRENT_YEAR % 100:02d}"
    features = [
        _feature("BA", "24", "01", 100.0),
        _feature("BA", "24", "02", 5.0, cl="nuvem"),  # não é alerta de desmatamento
        _feature("BA", current_year_2digit, "01", 999.0),  # ano corrente, incompleto
    ]

    def fake_get(url: str, headers: dict, timeout: float) -> httpx.Response:
        return httpx.Response(200, json=_response(features), request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    by_state = fetch_area_desmatada_by_state()

    assert by_state["BA"] == [SeriesPoint(reference_date=date(2024, 1, 1), value=100.0)]


def test_fetch_area_desmatada_brasil_sums_across_states(monkeypatch: pytest.MonkeyPatch) -> None:
    features = [
        _feature("BA", "24", "01", 100.0),
        _feature("GO", "24", "01", 20.0),
    ]

    def fake_get(url: str, headers: dict, timeout: float) -> httpx.Response:
        return httpx.Response(200, json=_response(features), request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    points = fetch_area_desmatada_brasil()

    assert points == [SeriesPoint(reference_date=date(2024, 1, 1), value=120.0)]
