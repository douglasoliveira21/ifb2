from datetime import date

import httpx
import pytest

from app.sync import leitos_sus_client
from app.sync.bcb_client import SeriesPoint
from app.sync.leitos_sus_client import (
    URL_TEMPLATE,
    fetch_leitos_sus_brasil,
    fetch_leitos_sus_by_state,
)


@pytest.fixture(autouse=True)
def _clear_download_cache():
    leitos_sus_client._download_year_csv.cache_clear()
    yield
    leitos_sus_client._download_year_csv.cache_clear()


_HEADER = (
    '"COMP","REGIAO","UF","MUNICIPIO","MOTIVO_DESABILITACAO","CNES","NOME_ESTABELECIMENTO",'
    '"RAZAO_SOCIAL","TP_GESTAO","CO_TIPO_UNIDADE","DS_TIPO_UNIDADE","NATUREZA_JURIDICA",'
    '"DESC_NATUREZA_JURIDICA","NO_LOGRADOURO","NU_ENDERECO","NO_COMPLEMENTO","NO_BAIRRO",'
    '"CO_CEP","NU_TELEFONE","NO_EMAIL",LEITOS_EXISTENTES,LEITOS_SUS,UTI_TOTAL_EXIST,'
    "UTI_TOTAL_SUS,UTI_ADULTO_EXIST,UTI_ADULTO_SUS,UTI_PEDIATRICO_EXIST,UTI_PEDIATRICO_SUS,"
    "UTI_NEONATAL_EXIST,UTI_NEONATAL_SUS,UTI_QUEIMADO_EXIST,UTI_QUEIMADO_SUS,"
    "UTI_CORONARIANA_EXIST,UTI_CORONARIANA_SUS"
)


def _row(comp: str, uf: str, leitos_sus) -> str:
    return f'"{comp}","SUDESTE","{uf}","CIDADE X",,"0000001","HOSPITAL X","RAZAO X","M","05","HOSPITAL GERAL","2062","HOSPITAL_PRIVADO","RUA X","1",,"BAIRRO",,"","",64,{leitos_sus},0,0,0,0,0,0,0,0,0,0,0,0'


def _csv_for_year(year: int) -> str:
    yy = str(year)
    rows = [
        _row(f"{yy}01", "SP", 100),
        _row(f"{yy}12", "SP", 150),
        _row(f"{yy}12", "SP", 50),
        _row(f"{yy}12", "MG", 30),
    ]
    return "\n".join([_HEADER, *rows])


def test_fetch_leitos_sus_by_state_sums_last_month_only(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, headers: dict, timeout: float, follow_redirects: bool) -> httpx.Response:
        if url == URL_TEMPLATE.format(year=2023):
            return httpx.Response(200, text=_csv_for_year(2023), request=httpx.Request("GET", url))
        return httpx.Response(403, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    by_state = fetch_leitos_sus_by_state(start_year=2023)

    assert by_state["SP"] == [SeriesPoint(reference_date=date(2023, 1, 1), value=200.0)]  # 150 + 50, só dez
    assert by_state["MG"] == [SeriesPoint(reference_date=date(2023, 1, 1), value=30.0)]


def test_fetch_leitos_sus_brasil_sums_all_states(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, headers: dict, timeout: float, follow_redirects: bool) -> httpx.Response:
        if url == URL_TEMPLATE.format(year=2023):
            return httpx.Response(200, text=_csv_for_year(2023), request=httpx.Request("GET", url))
        return httpx.Response(403, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    points = fetch_leitos_sus_brasil(start_year=2023)

    assert points == [SeriesPoint(reference_date=date(2023, 1, 1), value=230.0)]  # 200 (SP) + 30 (MG)


def test_fetch_leitos_sus_by_state_skips_unpublished_years(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, headers: dict, timeout: float, follow_redirects: bool) -> httpx.Response:
        return httpx.Response(403, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    assert fetch_leitos_sus_by_state(start_year=2023) == {}


def test_fetch_leitos_sus_by_state_retries_on_503_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    def fake_get(url: str, headers: dict, timeout: float, follow_redirects: bool) -> httpx.Response:
        calls["count"] += 1
        if url != URL_TEMPLATE.format(year=2023):
            return httpx.Response(403, request=httpx.Request("GET", url))
        if calls["count"] == 1:
            return httpx.Response(503, request=httpx.Request("GET", url))
        return httpx.Response(200, text=_csv_for_year(2023), request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr("app.sync.leitos_sus_client.time.sleep", lambda _: None)

    by_state = fetch_leitos_sus_by_state(start_year=2023)

    assert by_state["SP"] == [SeriesPoint(reference_date=date(2023, 1, 1), value=200.0)]
