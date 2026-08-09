from datetime import date

import httpx
import pytest

from app.sync.bcb_client import SeriesPoint, fetch_series, invert_sign, resample_to_month_end


def test_fetch_series_parses_and_converts_types(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = [
        {"data": "01/02/2026", "valor": "3.81"},
        {"data": "01/03/2026", "valor": "4.14"},
    ]

    def fake_get(url: str, params: dict, timeout: float) -> httpx.Response:
        return httpx.Response(200, json=payload, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    points = fetch_series(13522)

    assert points == [
        SeriesPoint(reference_date=date(2026, 2, 1), value=3.81),
        SeriesPoint(reference_date=date(2026, 3, 1), value=4.14),
    ]


def test_fetch_series_raises_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, params: dict, timeout: float) -> httpx.Response:
        request = httpx.Request("GET", url)
        return httpx.Response(500, request=request)

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(httpx.HTTPStatusError):
        fetch_series(432)


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
