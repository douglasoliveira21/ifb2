from datetime import date

import httpx
import pytest

from app.sync.bcb_client import SeriesPoint
from app.sync.tesouro_transferencias_client import (
    fetch_transferencias_constitucionais_by_municipio,
    fetch_transferencias_constitucionais_by_state,
)


def _response(registros: list[dict]) -> dict:
    return {"registros": registros, "status": "ok"}


def test_fetch_transferencias_constitucionais_sums_by_state_and_year(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registros = [
        {"transferencia": "FPE", "uf": "SP", "ano": "2023", "mes": "01", "valor": 100.0, "regiao": "Sudeste"},
        {"transferencia": "FUNDEB", "uf": "SP", "ano": "2023", "mes": "01", "valor": 200.0, "regiao": "Sudeste"},
        {"transferencia": "FPE", "uf": "SP", "ano": "2023", "mes": "02", "valor": 50.0, "regiao": "Sudeste"},
        {"transferencia": "FPE", "uf": "AC", "ano": "2023", "mes": "01", "valor": 10.0, "regiao": "Norte"},
        {"transferencia": "FPE", "uf": "SP", "ano": "2024", "mes": "01", "valor": 999.0, "regiao": "Sudeste"},
    ]

    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        return httpx.Response(200, json=_response(registros), request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    by_state = fetch_transferencias_constitucionais_by_state(start_year=2023)

    assert by_state["SP"] == [
        SeriesPoint(reference_date=date(2023, 1, 1), value=350.0),
        SeriesPoint(reference_date=date(2024, 1, 1), value=999.0),
    ]
    assert by_state["AC"] == [SeriesPoint(reference_date=date(2023, 1, 1), value=10.0)]


def test_fetch_transferencias_constitucionais_sends_expected_params(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen_params: list[dict] = []

    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        seen_params.append(params)
        return httpx.Response(200, json=_response([]), request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    fetch_transferencias_constitucionais_by_state(start_year=2023)

    assert len(seen_params) == 1
    assert seen_params[0]["p_estado"] == ":".join(str(i) for i in range(1, 28))
    assert seen_params[0]["p_ano"].startswith("2023:")


def test_fetch_transferencias_constitucionais_returns_empty_when_no_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        return httpx.Response(200, json=_response([]), request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    assert fetch_transferencias_constitucionais_by_state(start_year=2023) == {}


def test_fetch_transferencias_constitucionais_retries_on_503_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"count": 0}
    registros = [{"transferencia": "FPE", "uf": "SP", "ano": "2023", "mes": "01", "valor": 42.0, "regiao": "Sudeste"}]

    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        calls["count"] += 1
        request = httpx.Request("GET", url)
        if calls["count"] == 1:
            return httpx.Response(503, request=request)
        return httpx.Response(200, json=_response(registros), request=request)

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr("app.sync.tesouro_transferencias_client.time.sleep", lambda _: None)

    by_state = fetch_transferencias_constitucionais_by_state(start_year=2023)

    assert calls["count"] == 2
    assert by_state == {"SP": [SeriesPoint(reference_date=date(2023, 1, 1), value=42.0)]}


def test_fetch_transferencias_constitucionais_raises_on_persistent_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        return httpx.Response(500, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr("app.sync.tesouro_transferencias_client.time.sleep", lambda _: None)

    with pytest.raises(httpx.HTTPStatusError):
        fetch_transferencias_constitucionais_by_state(start_year=2023)


def _municipio_response(registros: list[dict]) -> dict:
    return {"registros": registros, "status": "ok", "page": 1, "pageSize": 100000, "next": None}


def test_fetch_transferencias_constitucionais_by_municipio_sums_by_codigo_ibge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        request = httpx.Request("GET", url)
        if params["p_estado"] == 26:  # SP
            registros = [
                {"UF": "SP", "ANO": "2023", "TRANSFERENCIA": "FPM", "CO_IBGE": 3550308, "MES": "01", "MUNICIPIO": "São Paulo", "VALOR": 100.0},
                {"UF": "SP", "ANO": "2023", "TRANSFERENCIA": "FUNDEB", "CO_IBGE": 3550308, "MES": "01", "MUNICIPIO": "São Paulo", "VALOR": 200.0},
                {"UF": "SP", "ANO": "2023", "TRANSFERENCIA": "FPM", "CO_IBGE": 3509502, "MES": "01", "MUNICIPIO": "Campinas", "VALOR": 50.0},
            ]
            return httpx.Response(200, json=_municipio_response(registros), request=request)
        return httpx.Response(200, json=_municipio_response([]), request=request)

    monkeypatch.setattr(httpx, "get", fake_get)

    by_municipio = fetch_transferencias_constitucionais_by_municipio(year=2023)

    assert by_municipio["3550308"] == [SeriesPoint(reference_date=date(2023, 1, 1), value=300.0)]
    assert by_municipio["3509502"] == [SeriesPoint(reference_date=date(2023, 1, 1), value=50.0)]


def test_fetch_transferencias_constitucionais_by_municipio_defaults_to_last_complete_year(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen_years: list[int] = []

    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        seen_years.append(params["p_ano"])
        return httpx.Response(200, json=_municipio_response([]), request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    fetch_transferencias_constitucionais_by_municipio()

    assert len(seen_years) == 27
    assert all(y == date.today().year - 1 for y in seen_years)
