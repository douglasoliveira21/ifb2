"""Cliente para o CEIS (Cadastro Nacional de Empresas Inidôneas e
Suspensas) — Portal da Transparência do Governo Federal (CGU).

**Download direto, sem chave de API**: diferente da API REST do Portal
da Transparência (que exige cadastro), o download em massa
(`/download-de-dados/ceis/{AAAAMMDD}`) é público — mas só aceita a
data de hoje (`date.today()`), confirmado empiricamente (datas
anteriores devolvem 403). O portal gera um novo arquivo por dia; não
há um arquivo histórico consolidado para baixar de uma vez, mesma
limitação já documentada para a base do SISDEPEN
(`sisdepen_client.py`) — mas aqui o efeito é o oposto: como o sync
roda periodicamente e cada execução pega o snapshot do dia, o
histórico vai se formando naturalmente a cada sync, um ponto por dia
de execução (não é uma série retroativa completa).

**Sanção "ativa"**: a coluna `DATA FINAL SANÇÃO` vem vazia quando a
sanção não tem prazo definido (ex: improbidade administrativa, sem
prazo determinado) — nesses casos o IFB conta como ativa. Quando
preenchida, é ativa só se a data for igual ou posterior a hoje.

**UF é do órgão que aplicou a sanção, não da empresa sancionada**: a
única localização geográfica disponível no arquivo é a UF do órgão
sancionador (`UF ÓRGÃO SANCIONADOR`) — uma empresa de São Paulo pode
estar sancionada por um órgão do Rio de Janeiro, por exemplo. Este
indicador mede onde a fiscalização aconteceu, não onde as empresas
sancionadas estão sediadas.

Conferido: 13/08/2026, 22.944 sanções ativas em 23.496 registros
totais do arquivo, SP a UF com mais sanções ativas (4.313) — coerente
com SP ser o estado com mais órgãos públicos e mais atividade
econômica do país.
"""
import csv
import io
import zipfile
from collections import Counter
from datetime import date, datetime

import httpx

from app.sync.bcb_client import SeriesPoint

REQUEST_HEADERS = {
    "User-Agent": "IFB-Sync/1.0 (+https://github.com/douglasoliveira21/ifb2)",
}

CEIS_URL_TEMPLATE = "https://portaldatransparencia.gov.br/download-de-dados/ceis/{data}"

COLUNA_UF = "UF ÓRGÃO SANCIONADOR"
COLUNA_DATA_FINAL = "DATA FINAL SANÇÃO"


def _is_ativa(data_final: str, *, hoje: date) -> bool:
    data_final = (data_final or "").strip()
    if not data_final:
        return True  # sem prazo definido = sanção permanente/indeterminada
    try:
        return datetime.strptime(data_final, "%d/%m/%Y").date() >= hoje
    except ValueError:
        return True  # data malformada — não descarta a sanção por causa disso


def _count_ativas(url: str, *, hoje: date, timeout: float) -> tuple[int, Counter]:
    """Retorna (total_ativas_brasil, contagem_por_uf) — o total inclui
    sanções sem UF do órgão sancionador informada; a contagem por
    estado, não (não há para onde atribuí-las)."""
    response = httpx.get(url, headers=REQUEST_HEADERS, timeout=timeout, follow_redirects=True)
    response.raise_for_status()
    zf = zipfile.ZipFile(io.BytesIO(response.content))
    with zf.open(zf.namelist()[0]) as f:
        text = f.read().decode("cp1252")
    reader = csv.DictReader(io.StringIO(text), delimiter=";", quotechar='"')

    total = 0
    by_uf: Counter = Counter()
    for row in reader:
        if not _is_ativa(row.get(COLUNA_DATA_FINAL, ""), hoje=hoje):
            continue
        total += 1
        uf = (row.get(COLUNA_UF) or "").strip()
        if uf:
            by_uf[uf] += 1
    return total, by_uf


def fetch_sancoes_ativas_ceis_by_state(*, timeout: float = 60.0) -> dict[str, list[SeriesPoint]]:
    hoje = date.today()
    url = CEIS_URL_TEMPLATE.format(data=hoje.strftime("%Y%m%d"))
    _total, by_uf = _count_ativas(url, hoje=hoje, timeout=timeout)
    return {uf: [SeriesPoint(reference_date=hoje, value=float(total))] for uf, total in by_uf.items()}


def fetch_sancoes_ativas_ceis_brasil(*, timeout: float = 60.0) -> list[SeriesPoint]:
    hoje = date.today()
    url = CEIS_URL_TEMPLATE.format(data=hoje.strftime("%Y%m%d"))
    total, _by_uf = _count_ativas(url, hoje=hoje, timeout=timeout)
    return [SeriesPoint(reference_date=hoje, value=float(total))]
