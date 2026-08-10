import io
import zipfile
from datetime import date

import httpx
import openpyxl
import pytest

from app.sync.bcb_client import SeriesPoint
from app.sync.inep_client import IdebSheetSpec, _cached_xlsx_bytes, fetch_ideb_series


@pytest.fixture(autouse=True)
def _clear_ideb_cache():
    _cached_xlsx_bytes.cache_clear()
    yield
    _cached_xlsx_bytes.cache_clear()


def _build_ideb_zip() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Brasil (Anos Iniciais)"

    # Linhas antes do cabeçalho — título, notas etc, como na planilha real.
    ws.append(["Ministério da Educação"])
    ws.append(["Ensino Fundamental Regular"])
    ws.append([])

    header = ["Brasil", "Rede"] + [f"VL_APROVACAO_2005_SI_{i}" for i in range(3)]
    header += ["VL_OBSERVADO_2005", "VL_OBSERVADO_2007", "VL_OBSERVADO_2021"]
    ws.append(header)

    row_estadual = ["Brasil", "Estadual"] + [None] * 3 + [3.0, 3.2, 3.5]
    row_total = ["Brasil", "Total"] + [None] * 3 + [3.8, 4.2, 5.8]
    ws.append(row_estadual)
    ws.append(row_total)

    xlsx_buffer = io.BytesIO()
    wb.save(xlsx_buffer)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("divulgacao_brasil_ideb_2025.xlsx", xlsx_buffer.getvalue())
        zf.writestr("divulgacao_brasil_ideb_2025.md5", "fakehash")

    return zip_buffer.getvalue()


def test_fetch_ideb_series_reads_total_row(monkeypatch: pytest.MonkeyPatch) -> None:
    zip_bytes = _build_ideb_zip()

    def fake_get(url: str, headers: dict, timeout: float, follow_redirects: bool) -> httpx.Response:
        return httpx.Response(200, content=zip_bytes, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    spec = IdebSheetSpec(zip_url="https://example.org/ideb.zip", sheet_name="Brasil (Anos Iniciais)")
    points = fetch_ideb_series(spec)

    assert points == [
        SeriesPoint(reference_date=date(2005, 1, 1), value=3.8),
        SeriesPoint(reference_date=date(2007, 1, 1), value=4.2),
        SeriesPoint(reference_date=date(2021, 1, 1), value=5.8),
    ]


def test_fetch_ideb_series_retries_on_connection_reset_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    zip_bytes = _build_ideb_zip()
    calls = {"count": 0}

    def fake_get(url: str, headers: dict, timeout: float, follow_redirects: bool) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            raise httpx.ConnectError("connection reset by peer", request=httpx.Request("GET", url))
        return httpx.Response(200, content=zip_bytes, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr("app.sync.inep_client.time.sleep", lambda _seconds: None)

    spec = IdebSheetSpec(zip_url="https://example.org/ideb-retry.zip", sheet_name="Brasil (Anos Iniciais)")
    points = fetch_ideb_series(spec)

    assert calls["count"] == 2
    assert points[0] == SeriesPoint(reference_date=date(2005, 1, 1), value=3.8)


def test_fetch_ideb_series_missing_sheet_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    zip_bytes = _build_ideb_zip()

    def fake_get(url: str, headers: dict, timeout: float, follow_redirects: bool) -> httpx.Response:
        return httpx.Response(200, content=zip_bytes, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    spec = IdebSheetSpec(zip_url="https://example.org/ideb.zip", sheet_name="Brasil (EM)")
    with pytest.raises(KeyError):
        fetch_ideb_series(spec)
