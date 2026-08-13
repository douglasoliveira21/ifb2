"""Cliente para o número de Defensores Públicos por estado — Pesquisa
Nacional da Defensoria Pública (ANADEP + Fórum Nacional de Defensores
Públicos Gerais), publicada em pesquisanacionaldefensoria.com.br.

Diferente do relatório em PDF do mesmo levantamento (que só traz os
números por estado como mapa/imagem, não como texto ou tabela
extraível), a página "Base de Dados" do site disponibiliza a planilha
completa (`.xlsx`) usada para produzir o relatório — com uma série
anual por estado desde 2003 (irregular nos anos mais antigos, anual e
completa a partir de 2020).

**Fonte não-governamental**: como o FBSP (já usado em
`fbsp_client.py`), a Pesquisa Nacional da Defensoria Pública é
produzida por uma associação de classe (ANADEP), não por um órgão do
governo — mas é o levantamento de referência do setor, feito em
cooperação direta com as Defensorias Públicas estaduais que fornecem
os próprios dados administrativos (não é uma pesquisa de opinião nem
uma estimativa).

**Não é "Defensores por 100 mil habitantes" pronto**: a planilha traz
só a contagem de Defensores; o IFB combina com a população do IBGE
(mesmo padrão de `_ratio_series_by_state` em `run.py`) para calcular a
razão.

Conferido: Brasil (soma dos 27 estados + DF, sem contar a União/DPU)
2024 = 6.917 Defensores Públicos estaduais.
"""
import io
from datetime import date

import httpx
import openpyxl

from app.sync.bcb_client import SeriesPoint

REQUEST_HEADERS = {
    "User-Agent": "IFB-Sync/1.0 (+https://github.com/douglasoliveira21/ifb2)",
}

DEFENSORIA_XLSX_URL = (
    "https://pesquisanacionaldefensoria.com.br/download/"
    "bases_de_dados_da_pesquisa_nacional_da_defensoria_publica-2025.xlsx"
)
SHEET_NAME = "Relatório Administrativo"

COL_ESTADO = 0
COL_ANO = 1
COL_DPT = 3  # "003_0.DPT" — Número de Defensores Públicos (total)

_STATE_NAME_TO_UF = {
    "Acre": "AC", "Alagoas": "AL", "Amapá": "AP", "Amazonas": "AM", "Bahia": "BA",
    "Ceará": "CE", "Distrito Federal": "DF", "Espírito Santo": "ES", "Goiás": "GO",
    "Maranhão": "MA", "Mato Grosso": "MT", "Mato Grosso do Sul": "MS", "Minas Gerais": "MG",
    "Pará": "PA", "Paraíba": "PB", "Paraná": "PR", "Pernambuco": "PE", "Piauí": "PI",
    "Rio de Janeiro": "RJ", "Rio Grande do Norte": "RN", "Rio Grande do Sul": "RS",
    "Rondônia": "RO", "Roraima": "RR", "Santa Catarina": "SC", "São Paulo": "SP",
    "Sergipe": "SE", "Tocantins": "TO",
}


def fetch_defensores_publicos_by_state(
    url: str = DEFENSORIA_XLSX_URL, *, timeout: float = 60.0
) -> dict[str, list[SeriesPoint]]:
    response = httpx.get(url, headers=REQUEST_HEADERS, timeout=timeout, follow_redirects=True)
    response.raise_for_status()
    wb = openpyxl.load_workbook(io.BytesIO(response.content), read_only=True, data_only=True)
    ws = wb[SHEET_NAME]

    by_state: dict[str, list[SeriesPoint]] = {}
    for row in ws.iter_rows(min_row=5, values_only=True):
        estado = row[COL_ESTADO]
        uf = _STATE_NAME_TO_UF.get(estado)
        if uf is None:  # "União" (Defensoria Pública da União) não é um estado
            continue
        ano = row[COL_ANO]
        dpt = row[COL_DPT]
        if not isinstance(ano, int) or not isinstance(dpt, (int, float)):
            continue
        by_state.setdefault(uf, []).append(SeriesPoint(reference_date=date(ano, 1, 1), value=float(dpt)))

    for points in by_state.values():
        points.sort(key=lambda p: p.reference_date)
    return by_state
