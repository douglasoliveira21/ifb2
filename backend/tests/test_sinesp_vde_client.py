import io
from datetime import date

import httpx
import openpyxl
import pytest

from app.sync.bcb_client import SeriesPoint
from app.sync.sinesp_vde_client import (
    _download_year_workbook_bytes,
    fetch_homicidio_doloso_brasil,
    fetch_homicidio_doloso_by_state,
)


@pytest.fixture(autouse=True)
def _clear_download_cache():
    _download_year_workbook_bytes.cache_clear()
    yield
    _download_year_workbook_bytes.cache_clear()

HEADER = [
    "uf", "municipio", "evento", "data_referencia", "agente", "arma", "faixa_etaria",
    "feminino", "masculino", "nao_informado", "total_vitima", "total", "total_peso", "abrangencia",
]


def _workbook_bytes(rows: list[list]) -> bytes:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "2024"
    sheet.append(HEADER)
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _row(uf: str, evento: str, total_vitima: int) -> list:
    return [uf, "MUNICIPIO", evento, "2024-01-01", None, None, None, 0, 0, 0, total_vitima, None, None, "Estadual"]


def test_fetch_homicidio_doloso_by_state_sums_only_matching_evento(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = _workbook_bytes(
        [
            _row("BA", "Homicídio doloso", 100),
            _row("BA", "Homicídio doloso", 50),
            _row("BA", "Roubo de veículo", 999),  # não deve entrar na soma
            _row("SP", "Homicídio doloso", 30),
        ]
    )

    def fake_get(url: str, headers: dict, timeout: float, follow_redirects: bool) -> httpx.Response:
        assert "User-Agent" in headers
        if "2024" not in url:
            return httpx.Response(403, request=httpx.Request("GET", url))
        return httpx.Response(200, content=content, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    by_state = fetch_homicidio_doloso_by_state(start_year=2024)

    assert by_state["BA"] == [SeriesPoint(reference_date=date(2024, 1, 1), value=150.0)]
    assert by_state["SP"] == [SeriesPoint(reference_date=date(2024, 1, 1), value=30.0)]


def test_fetch_homicidio_doloso_brasil_sums_across_states(monkeypatch: pytest.MonkeyPatch) -> None:
    content = _workbook_bytes(
        [
            _row("BA", "Homicídio doloso", 100),
            _row("SP", "Homicídio doloso", 30),
        ]
    )

    def fake_get(url: str, headers: dict, timeout: float, follow_redirects: bool) -> httpx.Response:
        if "2024" not in url:
            return httpx.Response(403, request=httpx.Request("GET", url))
        return httpx.Response(200, content=content, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    points = fetch_homicidio_doloso_brasil(start_year=2024)

    assert points == [SeriesPoint(reference_date=date(2024, 1, 1), value=130.0)]


def test_fetch_homicidio_doloso_skips_year_not_yet_published(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, headers: dict, timeout: float, follow_redirects: bool) -> httpx.Response:
        return httpx.Response(403, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    assert fetch_homicidio_doloso_brasil(start_year=2024) == []
