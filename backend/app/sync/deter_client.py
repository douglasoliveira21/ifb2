"""Cliente para o DETER Cerrado (INPE/TerraBrasilis) — alertas de
desmatamento por satélite no bioma Cerrado, agregados mensalmente por
estado.

**Contexto da descoberta**: o dashboard PRODES Cerrado (`app/sync/`
não tem um cliente próprio para ele por causa disso) tem um bug
confirmado — a página carrega o arquivo de taxas da Amazônia Legal em
vez do Cerrado, então o PRODES Cerrado não é usado no IFB. O DETER
Cerrado é uma fonte diferente do mesmo INPE: em vez do dashboard
"Gráficos" (com bug), usa o endpoint de entrega de arquivo por trás do
dashboard "avisos de Desmatamento" — `file-delivery/download/deter-
cerrado-nb/monthly` — descoberto inspecionando as chamadas de rede
desse dashboard (mesma técnica que já tinha funcionado para achar o
arquivo de taxas do PRODES Amazônia Legal).

Diferente do PRODES (recorte anual oficial, consolidado, comparável
ano a ano), o **DETER é um sistema de alerta quase em tempo real** —
mais rápido, mas com metodologia diferente (não é a mesma medição
"oficial" usada para comparar desmatamento ano a ano). O IFB documenta
essa diferença explicitamente na metodologia do indicador; não deve
ser somado nem comparado diretamente ao indicador de desmatamento da
Amazônia Legal (que usa PRODES).

Ao contrário do PRODES (que expõe só o rateio anual pronto) e do WFS de
polígonos brutos do Cerrado (2,3 milhões de feições, sem agregação no
servidor — inviável para este projeto), este endpoint **já devolve a
área mensal agregada por estado**, pronta (campo `ar`, em km², e `np`,
número de polígonos) — sem geometria, um valor por mês/estado. O IFB
soma os meses de cada ano civil.

Validado ao vivo: soma nacional de 2024 = 5.901 km² (sob alerta do
DETER) — mesma ordem de grandeza da taxa oficial do PRODES para o
Cerrado no período 08/2023-07/2024 (8.174 km², amplamente noticiada),
com a diferença esperada entre os dois sistemas (períodos de referência
diferentes — DETER por ano civil, PRODES por ano agrícola de
agosto a julho — e metodologias diferentes, alerta rápido vs.
consolidação anual).
"""
from collections import defaultdict
from datetime import date

import httpx

from app.sync.bcb_client import SeriesPoint

URL = "https://terrabrasilis.dpi.inpe.br/file-delivery/download/deter-cerrado-nb/monthly"

REQUEST_HEADERS = {
    "User-Agent": "IFB-Sync/1.0 (+https://github.com/douglasoliveira21/ifb2)",
}


def _fetch_monthly_alert_area_by_state(*, timeout: float) -> dict[tuple[int, str], float]:
    """Retorna {(ano, uf): área somada de todos os meses daquele ano em
    km²} — o arquivo já vem por mês, o IFB soma os 12 meses de cada
    ano civil."""
    response = httpx.get(URL, headers=REQUEST_HEADERS, timeout=timeout)
    response.raise_for_status()
    data = response.json()

    by_year_uf: dict[tuple[int, str], float] = defaultdict(float)
    for feature in data["features"]:
        props = feature["properties"]
        if props.get("cl") != "alerta":
            continue
        year = 2000 + int(props["y"])
        uf = props["uf"]
        by_year_uf[(year, uf)] += float(props["ar"])

    return dict(by_year_uf)


def fetch_area_desmatada_by_state(*, timeout: float = 30.0) -> dict[str, list[SeriesPoint]]:
    """Área sob alerta de desmatamento (DETER) no Cerrado, por estado,
    um ponto por ano civil completo — o IFB descarta o ano corrente
    (incompleto, ainda em andamento)."""
    current_year = date.today().year
    by_year_uf = _fetch_monthly_alert_area_by_state(timeout=timeout)

    by_state: dict[str, list[SeriesPoint]] = defaultdict(list)
    for (year, uf), area in by_year_uf.items():
        if year >= current_year:
            continue
        by_state[uf].append(SeriesPoint(reference_date=date(year, 1, 1), value=round(area, 2)))

    for points in by_state.values():
        points.sort(key=lambda p: p.reference_date)

    return dict(by_state)


def fetch_area_desmatada_brasil(*, timeout: float = 30.0) -> list[SeriesPoint]:
    """Mesma série, somada para os 13 estados do bioma Cerrado."""
    current_year = date.today().year
    by_year_uf = _fetch_monthly_alert_area_by_state(timeout=timeout)

    totals_by_year: dict[int, float] = defaultdict(float)
    for (year, _uf), area in by_year_uf.items():
        if year >= current_year:
            continue
        totals_by_year[year] += area

    return sorted(
        (SeriesPoint(reference_date=date(year, 1, 1), value=round(total, 2)) for year, total in totals_by_year.items()),
        key=lambda p: p.reference_date,
    )
