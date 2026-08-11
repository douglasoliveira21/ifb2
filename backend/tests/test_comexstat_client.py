from datetime import date

import httpx
import pytest

from app.sync.bcb_client import SeriesPoint
from app.sync.comexstat_client import fetch_totals_brasil, fetch_totals_by_state


def _response(rows: list[dict]) -> dict:
    return {"data": {"list": rows}, "success": True, "message": None}


def test_fetch_totals_brasil_parses_and_sorts_by_year(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        {"year": "2024", "metricFOB": "337046161710"},
        {"year": "2023", "metricFOB": "339695766008"},
    ]

    def fake_post(url: str, headers: dict, json: dict, timeout: float) -> httpx.Response:
        assert json["flow"] == "export"
        return httpx.Response(200, json=_response(rows), request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)

    points = fetch_totals_brasil("export", start_year=2023, end_year=2024)

    assert points == [
        SeriesPoint(reference_date=date(2023, 1, 1), value=339_695_766_008.0),
        SeriesPoint(reference_date=date(2024, 1, 1), value=337_046_161_710.0),
    ]


def test_fetch_totals_by_state_maps_names_and_skips_nao_declarada(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        {"year": "2024", "state": "São Paulo", "metricFOB": "71406470352"},
        {"year": "2024", "state": "Rio de Janeiro", "metricFOB": "45771497130"},
        {"year": "2024", "state": "Não Declarada", "metricFOB": "5047544756"},
    ]

    def fake_post(url: str, headers: dict, json: dict, timeout: float) -> httpx.Response:
        assert json["details"] == ["state"]
        return httpx.Response(200, json=_response(rows), request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)

    by_state = fetch_totals_by_state("export", start_year=2024, end_year=2024)

    assert by_state == {
        "SP": [SeriesPoint(reference_date=date(2024, 1, 1), value=71_406_470_352.0)],
        "RJ": [SeriesPoint(reference_date=date(2024, 1, 1), value=45_771_497_130.0)],
    }


def test_fetch_totals_retries_on_429_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    def fake_post(url: str, headers: dict, json: dict, timeout: float) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] < 3:
            return httpx.Response(
                429,
                json={"error": {"code": 429, "message": "rate limited"}},
                request=httpx.Request("POST", url),
            )
        return httpx.Response(
            200,
            json=_response([{"year": "2024", "metricFOB": "100"}]),
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr("app.sync.comexstat_client.time.sleep", lambda _seconds: None)

    points = fetch_totals_brasil("export", start_year=2024, end_year=2024)

    assert calls["count"] == 3
    assert points == [SeriesPoint(reference_date=date(2024, 1, 1), value=100.0)]
