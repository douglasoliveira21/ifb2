import io
from datetime import date

import httpx
import openpyxl
import pytest

from app.sync.bcb_client import SeriesPoint
from app.sync.fbsp_client import FbspAnuarioSpec, fetch_mvi_rate_brasil, fetch_mvi_rate_by_state


def _build_workbook_bytes() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "T01"

    # Linhas 1-10 são cabeçalho/rótulos (irrelevantes para o parser, que só
    # olha a partir da linha 11) — deixadas em branco de propósito, igual
    # ao arquivo real.
    for _ in range(10):
        ws.append([None])

    # col A = nome, colunas N/O (14/15) = taxa 2023/2024 — mesmas posições
    # usadas pelo parser real.
    def row(name: str, taxa_2023: float, taxa_2024: float) -> list:
        values = [None] * 15
        values[0] = name
        values[13] = taxa_2023
        values[14] = taxa_2024
        return values

    ws.append(row("Brasil", 21.9, 20.8))
    ws.append([None])
    ws.append(row("Acre", 24.4, 20.3))
    ws.append(row("Bahia", 44.4, 40.6))
    ws.append(row("Minas Gerais (4)", 14.4, 15.1))  # sufixo de nota de rodapé
    ws.append(row("Nota de rodapé qualquer", 1.0, 2.0))  # não bate com nenhuma UF — deve ser ignorada

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_fetch_mvi_rate_by_state_parses_states_and_strips_footnote_suffix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = _build_workbook_bytes()

    def fake_get(url: str, headers: dict, timeout: float, follow_redirects: bool) -> httpx.Response:
        return httpx.Response(200, content=content, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    by_state = fetch_mvi_rate_by_state(FbspAnuarioSpec(url="https://example.test/anuario.xlsx"))

    assert by_state["AC"] == [
        SeriesPoint(reference_date=date(2023, 1, 1), value=24.4),
        SeriesPoint(reference_date=date(2024, 1, 1), value=20.3),
    ]
    assert by_state["BA"][1].value == 40.6
    assert by_state["MG"][0].value == 14.4  # sufixo "(4)" removido do nome antes de casar com a UF
    assert "Brasil" not in by_state
    assert len(by_state) == 3  # AC, BA, MG — a linha de nota de rodapé é ignorada


def test_fetch_mvi_rate_brasil_reads_only_brasil_row(monkeypatch: pytest.MonkeyPatch) -> None:
    content = _build_workbook_bytes()

    def fake_get(url: str, headers: dict, timeout: float, follow_redirects: bool) -> httpx.Response:
        return httpx.Response(200, content=content, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    points = fetch_mvi_rate_brasil(FbspAnuarioSpec(url="https://example.test/anuario.xlsx"))

    assert points == [
        SeriesPoint(reference_date=date(2023, 1, 1), value=21.9),
        SeriesPoint(reference_date=date(2024, 1, 1), value=20.8),
    ]


def test_fetch_mvi_rate_by_state_retries_on_503_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    content = _build_workbook_bytes()
    calls = {"count": 0}

    def fake_get(url: str, headers: dict, timeout: float, follow_redirects: bool) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(503, request=httpx.Request("GET", url))
        return httpx.Response(200, content=content, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr("app.sync.fbsp_client.time.sleep", lambda _: None)

    by_state = fetch_mvi_rate_by_state(FbspAnuarioSpec(url="https://example.test/anuario-retry.xlsx"))

    assert calls["count"] == 2
    assert "AC" in by_state
