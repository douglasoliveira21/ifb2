from datetime import date

import httpx
import pytest

from app.sync.bcb_client import SeriesPoint
from app.sync.siconfi_client import (
    DESPESA_COM_PESSOAL_RCL,
    DIVIDA_CONSOLIDADA_LIQUIDA_RCL,
    RECEITA_TOTAL_REALIZADA,
    fetch_rgf_by_municipio,
    fetch_rgf_by_state,
    fetch_rreo_by_state,
)


def _rgf_response(items: list[dict]) -> dict:
    return {"items": items, "hasMore": False, "limit": 5000, "offset": 0, "count": len(items)}


def _divida_rows(value: float) -> list[dict]:
    return [
        {"cod_conta": "PercentualDaDCLSobreARCL", "coluna": "SALDO DO EXERCICIO ANTERIOR", "valor": 10.0},
        {"cod_conta": "PercentualDaDCLSobreARCL", "coluna": "Ate o 1o Quadrimestre", "valor": 11.0},
        {"cod_conta": "PercentualDaDCLSobreARCL", "coluna": "Ate o 2o Quadrimestre", "valor": 12.0},
        {"cod_conta": "PercentualDaDCLSobreARCL", "coluna": "Ate o 3o Quadrimestre", "valor": value},
    ]


def _pessoal_rows(value: float) -> list[dict]:
    return [
        {"cod_conta": "DespesaComPessoalTotal", "coluna": "Valor", "valor": 1_000_000.0},
        {"cod_conta": "DespesaComPessoalTotal", "coluna": "% sobre a RCL Ajustada", "valor": value},
    ]


def test_fetch_rgf_by_state_reads_divida_consolidada_quadrimestre_3(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        # SP (id_ente=35) em qualquer ano tem dado; demais entes, nenhum —
        # simula uma fonte real onde só parte dos estados/anos tem valor.
        if params["id_ente"] == 35 and params["an_exercicio"] == 2023:
            payload = _rgf_response(_divida_rows(127.92))
        else:
            payload = _rgf_response([])
        return httpx.Response(200, json=payload, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    by_state = fetch_rgf_by_state(DIVIDA_CONSOLIDADA_LIQUIDA_RCL, start_year=2023)

    assert by_state == {"SP": [SeriesPoint(reference_date=date(2023, 1, 1), value=127.92)]}


def test_fetch_rgf_by_state_reads_despesa_com_pessoal_percentual(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        if params["id_ente"] == 35 and params["an_exercicio"] == 2023:
            payload = _rgf_response(_pessoal_rows(42.33))
        else:
            payload = _rgf_response([])
        return httpx.Response(200, json=payload, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    by_state = fetch_rgf_by_state(DESPESA_COM_PESSOAL_RCL, start_year=2023)

    assert by_state == {"SP": [SeriesPoint(reference_date=date(2023, 1, 1), value=42.33)]}


def test_fetch_rgf_by_state_skips_states_without_data(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        return httpx.Response(200, json=_rgf_response([]), request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    by_state = fetch_rgf_by_state(DIVIDA_CONSOLIDADA_LIQUIDA_RCL, start_year=2023)

    assert by_state == {}


def test_fetch_rgf_by_state_retries_on_503_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    calls_for_sp_2023 = {"count": 0}

    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        request = httpx.Request("GET", url)
        if params["id_ente"] != 35 or params["an_exercicio"] != 2023:
            return httpx.Response(200, json=_rgf_response([]), request=request)
        calls_for_sp_2023["count"] += 1
        if calls_for_sp_2023["count"] == 1:
            return httpx.Response(503, request=request)
        return httpx.Response(200, json=_rgf_response(_divida_rows(127.92)), request=request)

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr("app.sync.siconfi_client.time.sleep", lambda _: None)

    by_state = fetch_rgf_by_state(DIVIDA_CONSOLIDADA_LIQUIDA_RCL, start_year=2023)

    assert by_state == {"SP": [SeriesPoint(reference_date=date(2023, 1, 1), value=127.92)]}


def test_fetch_rgf_by_state_raises_on_persistent_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        return httpx.Response(500, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr("app.sync.siconfi_client.time.sleep", lambda _: None)

    with pytest.raises(httpx.HTTPStatusError):
        fetch_rgf_by_state(DIVIDA_CONSOLIDADA_LIQUIDA_RCL, start_year=2023)


def _rreo_response(items: list[dict]) -> dict:
    return {"items": items, "hasMore": False, "limit": 5000, "offset": 0, "count": len(items)}


def _receita_rows(value: float) -> list[dict]:
    return [
        {"cod_conta": "TotalReceitas", "coluna": "PREVISAO INICIAL", "valor": 1_000.0},
        {"cod_conta": "TotalReceitas", "coluna": "PREVISAO ATUALIZADA (a)", "valor": 1_100.0},
        {"cod_conta": "TotalReceitas", "coluna": "No Bimestre (b)", "valor": 200.0},
        {"cod_conta": "TotalReceitas", "coluna": "Ate o Bimestre (c)", "valor": value},
    ]


def test_fetch_rreo_by_state_reads_receita_total_ate_o_bimestre(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        if params["id_ente"] == 35 and params["an_exercicio"] == 2023:
            payload = _rreo_response(_receita_rows(326_742_547_158.85))
        else:
            payload = _rreo_response([])
        return httpx.Response(200, json=payload, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    by_state = fetch_rreo_by_state(RECEITA_TOTAL_REALIZADA, start_year=2023)

    assert by_state == {"SP": [SeriesPoint(reference_date=date(2023, 1, 1), value=326_742_547_158.85)]}


def test_fetch_rreo_by_state_does_not_confuse_no_bimestre_with_ate_o_bimestre(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """'No Bimestre (b)' e 'Ate o Bimestre (c)' compartilham a palavra
    'Bimestre' — o match precisa distinguir pelo marcador '(c)', não
    confundir com o valor do bimestre isolado."""

    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        if params["id_ente"] == 35 and params["an_exercicio"] == 2023:
            payload = _rreo_response(_receita_rows(999.0))
        else:
            payload = _rreo_response([])
        return httpx.Response(200, json=payload, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    by_state = fetch_rreo_by_state(RECEITA_TOTAL_REALIZADA, start_year=2023)

    assert by_state["SP"][0].value == 999.0  # não 200.0 ("No Bimestre")


def test_fetch_rreo_by_state_skips_states_without_data(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        return httpx.Response(200, json=_rreo_response([]), request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    assert fetch_rreo_by_state(RECEITA_TOTAL_REALIZADA, start_year=2023) == {}


def test_fetch_rgf_by_municipio_reads_single_year_per_codigo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.sync.siconfi_client.fetch_municipio_codes", lambda: ["3550308", "3509502"]
    )

    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        request = httpx.Request("GET", url)
        if params["id_ente"] == 3550308 and params["an_exercicio"] == 2023:
            return httpx.Response(200, json=_rgf_response(_pessoal_rows(29.98)), request=request)
        return httpx.Response(200, json=_rgf_response([]), request=request)

    monkeypatch.setattr(httpx, "get", fake_get)

    by_municipio = fetch_rgf_by_municipio(DESPESA_COM_PESSOAL_RCL, year=2023)

    assert by_municipio == {"3550308": [SeriesPoint(reference_date=date(2023, 1, 1), value=29.98)]}


def test_fetch_rgf_by_municipio_defaults_to_last_complete_year(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.sync.siconfi_client.fetch_municipio_codes", lambda: ["3550308"])
    seen_years: list[int] = []

    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        seen_years.append(params["an_exercicio"])
        return httpx.Response(200, json=_rgf_response([]), request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    fetch_rgf_by_municipio(DESPESA_COM_PESSOAL_RCL)

    assert seen_years == [date.today().year - 1]
