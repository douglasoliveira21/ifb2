from datetime import date

import httpx
import pytest

from app.sync.bcb_client import SeriesPoint
from app.sync.inpe_client import fetch_prodes_by_state, fetch_prodes_legal_amazon

SAMPLE_PAYLOAD = {
    "periods": [
        {
            "startDate": {"year": 2019, "month": 8, "day": 1},
            "endDate": {"year": 2020, "month": 7, "day": 31},
            "features": [
                {"loi": 1, "loiname": 18278, "areas": [{"type": 1, "area": 706}]},
                {"loi": 1, "loiname": 18279, "areas": [{"type": 1, "area": 1512}]},
            ],
        },
        {
            "startDate": {"year": 2020, "month": 8, "day": 1},
            "endDate": {"year": 2021, "month": 7, "day": 31},
            "features": [
                {"loi": 1, "loiname": 18278, "areas": [{"type": 1, "area": 889}]},
                {"loi": 1, "loiname": 18279, "areas": [{"type": 1, "area": 2306}]},
            ],
        },
    ]
}


def test_fetch_prodes_sums_areas_per_period_using_end_year(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, timeout: float) -> httpx.Response:
        return httpx.Response(200, json=SAMPLE_PAYLOAD, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    points = fetch_prodes_legal_amazon()

    assert points == [
        SeriesPoint(reference_date=date(2020, 1, 1), value=2218.0),
        SeriesPoint(reference_date=date(2021, 1, 1), value=3195.0),
    ]


def test_fetch_prodes_by_state_splits_series_per_uf(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, timeout: float) -> httpx.Response:
        return httpx.Response(200, json=SAMPLE_PAYLOAD, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    by_state = fetch_prodes_by_state()

    assert by_state["AC"] == [
        SeriesPoint(reference_date=date(2020, 1, 1), value=706.0),
        SeriesPoint(reference_date=date(2021, 1, 1), value=889.0),
    ]
    assert by_state["AM"] == [
        SeriesPoint(reference_date=date(2020, 1, 1), value=1512.0),
        SeriesPoint(reference_date=date(2021, 1, 1), value=2306.0),
    ]
    assert by_state["PA"] == []
