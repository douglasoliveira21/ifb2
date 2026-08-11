from datetime import date

import httpx
import pytest

from app.sync.bcb_client import SeriesPoint
from app.sync.datajud_client import (
    STATE_TJ_ALIAS,
    fetch_processos_ajuizados_by_state,
    fetch_processos_ajuizados_series_brasil,
    fetch_processos_ajuizados_series_by_state,
)

COUNTS_BY_ALIAS = {"tjsp": 3_329_580, "tjrs": 1_473_514, "tjma": 565_250, "tjdft": 39_930}


def _response(total: int) -> dict:
    return {"hits": {"total": {"value": total, "relation": "eq"}}}


def _fake_post_for(counts_by_alias: dict[str, int]):
    def fake_post(url: str, headers: dict, json: dict, timeout: float) -> httpx.Response:
        alias = url.split("api_publica_")[1].split("/_search")[0]
        total = counts_by_alias.get(alias, 0)
        return httpx.Response(200, json=_response(total), request=httpx.Request("POST", url))

    return fake_post


def test_fetch_processos_ajuizados_by_state_covers_all_27_units(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "post", _fake_post_for(COUNTS_BY_ALIAS))

    counts = fetch_processos_ajuizados_by_state(2024)

    assert len(counts) == 27
    assert set(counts.keys()) == set(STATE_TJ_ALIAS.keys())
    assert counts["SP"] == 3_329_580
    assert counts["DF"] == 39_930


def test_fetch_processos_ajuizados_series_by_state_builds_one_point_per_year(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(httpx, "post", _fake_post_for(COUNTS_BY_ALIAS))

    series = fetch_processos_ajuizados_series_by_state(start_year=2023, end_year=2024)

    assert series["SP"] == [
        SeriesPoint(reference_date=date(2023, 1, 1), value=3_329_580.0),
        SeriesPoint(reference_date=date(2024, 1, 1), value=3_329_580.0),
    ]


def test_fetch_processos_ajuizados_series_brasil_sums_all_states(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "post", _fake_post_for({alias: 1 for alias in STATE_TJ_ALIAS.values()}))

    series = fetch_processos_ajuizados_series_brasil(start_year=2024, end_year=2024)

    assert series == [SeriesPoint(reference_date=date(2024, 1, 1), value=27.0)]
