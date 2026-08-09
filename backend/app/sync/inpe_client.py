"""Cliente para o arquivo de taxas anuais do PRODES (INPE) — TerraBrasilis.

Diferente do SGS/BCB, o PRODES não expõe uma série já agregada por ano: o
arquivo publicado traz um registro por "loi" (unidade territorial — aqui os
9 estados da Amazônia Legal) dentro de cada período de 12 meses (1º de agosto
a 31 de julho, convenção oficial do PRODES). O IFB soma as áreas para obter
a taxa anual consolidada do Brasil, e também mantém a série por estado.

Fonte descoberta e validada inspecionando as chamadas de rede do dashboard
oficial do TerraBrasilis (http://terrabrasilis.dpi.inpe.br) — o mesmo JSON
estático que alimenta os gráficos publicados pelo INPE. Os valores agregados
foram conferidos contra números oficiais amplamente divulgados (ex: período
08/2020–07/2021 soma exatamente 13.038 km², o recorde de desmatamento da
Amazônia Legal daquele ciclo).

O mapeamento de código de estado (`loiname`) para UF veio do arquivo de
configuração oficial do próprio painel:
https://terrabrasilis.dpi.inpe.br/app/prodes/dashboard/deforestation/files/config/loinames/prodes_legal_amazon.json
"""
from datetime import date

import httpx

from app.sync.bcb_client import SeriesPoint

RATES_URL = "https://terrabrasilis.dpi.inpe.br/app/prodes/dashboard/deforestation/files/rates2025.json"

# gid (loiname) -> sigla da UF, conforme config/loinames/prodes_legal_amazon.json
STATE_GID_TO_UF = {
    18277: "RO",
    18278: "AC",
    18279: "AM",
    18280: "RR",
    18281: "PA",
    18282: "AP",
    18283: "TO",
    18285: "MT",
    18288: "MA",
}


def fetch_prodes_raw(*, timeout: float = 30.0) -> dict:
    response = httpx.get(RATES_URL, timeout=timeout)
    response.raise_for_status()
    return response.json()


def fetch_prodes_legal_amazon(*, timeout: float = 30.0) -> list[SeriesPoint]:
    """Taxa anual consolidada (soma de todos os estados) por período PRODES.
    A data de referência usada é o ano final do período (ex: período
    08/2020–07/2021 vira 01/01/2021), convenção com a qual o PRODES rotula
    seus próprios resultados anuais."""
    raw = fetch_prodes_raw(timeout=timeout)
    return _sum_by_period(raw)


def fetch_prodes_by_state(*, timeout: float = 30.0) -> dict[str, list[SeriesPoint]]:
    """Taxa anual por estado da Amazônia Legal. Retorna um dict UF -> série
    (apenas os 9 estados cobertos pelo PRODES Amazônia Legal — os outros 18
    estados brasileiros não têm este indicador)."""
    raw = fetch_prodes_raw(timeout=timeout)
    by_state: dict[str, list[SeriesPoint]] = {uf: [] for uf in STATE_GID_TO_UF.values()}

    for period in raw["periods"]:
        reference_date = date(period["endDate"]["year"], 1, 1)
        for feature in period["features"]:
            uf = STATE_GID_TO_UF.get(feature["loiname"])
            if uf is None:
                continue
            area = sum(a["area"] for a in feature["areas"])
            by_state[uf].append(SeriesPoint(reference_date=reference_date, value=float(area)))

    return by_state


def _sum_by_period(raw: dict) -> list[SeriesPoint]:
    points: list[SeriesPoint] = []
    for period in raw["periods"]:
        total_area = sum(
            area["area"]
            for feature in period["features"]
            for area in feature["areas"]
        )
        reference_year = period["endDate"]["year"]
        points.append(SeriesPoint(reference_date=date(reference_year, 1, 1), value=float(total_area)))
    return points
