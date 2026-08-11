from datetime import date

import httpx
import pytest

from app.sync.pncp_client import _aggregate_by_ano_uf, fetch_contratacoes_publicadas

# As funções que leem/escrevem PncpSyncCheckpoint e PncpContratacaoTotal
# (_get_checkpoint, _set_checkpoint, _add_to_accumulated_totals,
# sync_pncp_incremental) usam upsert nativo do Postgres (ON CONFLICT) e
# não têm cobertura de teste automatizado aqui — o projeto não tem
# infraestrutura de banco de teste (nenhum outro módulo de sync testa
# escrita real em Postgres; todos testam só as funções puras que
# produzem SeriesPoint). Essas funções foram validadas por revisão de
# código e pelos mesmos testes manuais de sync já usados no resto do
# projeto.


def _item(uf: str, valor: float, data_publicacao: str) -> dict:
    return {
        "unidadeOrgao": {"ufSigla": uf},
        "valorTotalEstimado": valor,
        "dataPublicacaoPncp": data_publicacao,
    }


def test_fetch_contratacoes_publicadas_paginates_until_last_page(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.sync.pncp_client.time.sleep", lambda _seconds: None)
    pages = {
        1: {"data": [_item("SP", 100.0, "2026-01-01T10:00:00")], "totalPaginas": 3},
        2: {"data": [_item("SP", 200.0, "2026-01-02T10:00:00")], "totalPaginas": 3},
        3: {"data": [_item("RJ", 50.0, "2026-01-03T10:00:00")], "totalPaginas": 3},
    }
    seen_paginas: list[int] = []

    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        seen_paginas.append(params["pagina"])
        return httpx.Response(200, json=pages[params["pagina"]], request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    items = fetch_contratacoes_publicadas(6, date(2026, 1, 1), date(2026, 1, 3))

    assert seen_paginas == [1, 2, 3]
    assert len(items) == 3


def test_fetch_contratacoes_publicadas_sends_expected_params(monkeypatch: pytest.MonkeyPatch) -> None:
    seen_params: list[dict] = []

    def fake_get(url: str, params: dict, headers: dict, timeout: float) -> httpx.Response:
        seen_params.append(params)
        return httpx.Response(200, json={"data": [], "totalPaginas": 1}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    fetch_contratacoes_publicadas(6, date(2026, 1, 15), date(2026, 1, 20))

    assert seen_params == [
        {
            "dataInicial": "20260115",
            "dataFinal": "20260120",
            "codigoModalidadeContratacao": 6,
            "pagina": 1,
            "tamanhoPagina": 50,
        }
    ]


def test_aggregate_by_ano_uf_sums_and_skips_missing_value_or_uf() -> None:
    items = [
        _item("SP", 100.0, "2025-12-31T23:00:00"),
        _item("SP", 50.0, "2026-01-01T00:00:00"),
        _item("RJ", 30.0, "2026-01-01T00:00:00"),
        {"unidadeOrgao": {"ufSigla": "MG"}, "valorTotalEstimado": None, "dataPublicacaoPncp": "2026-01-01T00:00:00"},
        {"unidadeOrgao": {}, "valorTotalEstimado": 999.0, "dataPublicacaoPncp": "2026-01-01T00:00:00"},
    ]

    totals = _aggregate_by_ano_uf(items)

    assert totals == {
        (2025, "SP"): 100.0,
        (2026, "SP"): 50.0,
        (2026, "RJ"): 30.0,
    }
