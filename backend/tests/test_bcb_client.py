from datetime import date

import httpx
import pytest

from app.sync.bcb_client import (
    SeriesPoint,
    fetch_daily_series_chunked,
    fetch_series,
    invert_sign,
    resample_to_month_end,
)


def test_fetch_series_parses_and_converts_types(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = [
        {"data": "01/02/2026", "valor": "3.81"},
        {"data": "01/03/2026", "valor": "4.14"},
    ]

    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        return httpx.Response(200, json=payload, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    points = fetch_series(13522)

    assert points == [
        SeriesPoint(reference_date=date(2026, 2, 1), value=3.81),
        SeriesPoint(reference_date=date(2026, 3, 1), value=4.14),
    ]


def test_fetch_series_raises_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        request = httpx.Request("GET", url)
        return httpx.Response(500, request=request)

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr("app.sync.bcb_client.time.sleep", lambda _: None)

    with pytest.raises(httpx.HTTPStatusError):
        fetch_series(432)


def test_fetch_series_retries_on_503_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = [{"data": "01/02/2026", "valor": "14.00"}]
    calls = {"count": 0}

    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        calls["count"] += 1
        request = httpx.Request("GET", url)
        if calls["count"] == 1:
            return httpx.Response(503, request=request)
        return httpx.Response(200, json=payload, request=request)

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr("app.sync.bcb_client.time.sleep", lambda _: None)

    points = fetch_series(432)

    assert calls["count"] == 2
    assert points == [SeriesPoint(reference_date=date(2026, 2, 1), value=14.00)]


def test_fetch_series_does_not_retry_on_406(monkeypatch: pytest.MonkeyPatch) -> None:
    """406 numa série diária longa é um erro estrutural (janela > 10 anos),
    não passageiro — não faz sentido tentar de novo com os mesmos parâmetros."""
    calls = {"count": 0}

    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        calls["count"] += 1
        request = httpx.Request("GET", url)
        return httpx.Response(406, request=request)

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(httpx.HTTPStatusError):
        fetch_series(432)

    assert calls["count"] == 1


def test_fetch_daily_series_chunked_splits_by_ten_year_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    requested_windows: list[tuple[str, str]] = []

    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        requested_windows.append((params["dataInicial"], params["dataFinal"]))
        year = int(params["dataInicial"].split("/")[-1])
        payload = [{"data": f"01/06/{year}", "valor": "10.0"}]
        return httpx.Response(200, json=payload, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    points = fetch_daily_series_chunked(432, start_year=2000)

    # de 2000 até o ano atual, em blocos de 10 anos
    assert requested_windows[0] == ("01/01/2000", "31/12/2009")
    assert requested_windows[1] == ("01/01/2010", "31/12/2019")
    assert len(points) == len(requested_windows)


def test_resample_to_month_end_keeps_last_point_per_month() -> None:
    points = [
        SeriesPoint(reference_date=date(2026, 1, 5), value=13.75),
        SeriesPoint(reference_date=date(2026, 1, 20), value=13.75),
        SeriesPoint(reference_date=date(2026, 2, 3), value=13.25),
        SeriesPoint(reference_date=date(2026, 2, 28), value=13.0),
    ]

    resampled = resample_to_month_end(points)

    assert resampled == [
        SeriesPoint(reference_date=date(2026, 1, 1), value=13.75),
        SeriesPoint(reference_date=date(2026, 2, 1), value=13.0),
    ]


def test_invert_sign_flips_all_values() -> None:
    points = [
        SeriesPoint(reference_date=date(2020, 12, 1), value=9.79),
        SeriesPoint(reference_date=date(2021, 1, 1), value=-1.5),
    ]

    inverted = invert_sign(points)

    assert inverted == [
        SeriesPoint(reference_date=date(2020, 12, 1), value=-9.79),
        SeriesPoint(reference_date=date(2021, 1, 1), value=1.5),
    ]
