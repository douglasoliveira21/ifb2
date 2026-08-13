"""Cliente + acumulador incremental para o PNCP (Portal Nacional de
Contratações Públicas) — https://pncp.gov.br/api/consulta.

**Por que acumulação incremental, e não somar tudo a cada sync**: o PNCP
não expõe nenhum total agregado pronto — só registros individuais
paginados (50 por página). Uma única semana de uma única modalidade de
contratação já tem ~2.500 registros; somar o histórico inteiro do zero
a cada sync levaria dezenas de minutos e refaria trabalho já feito. Em
vez disso, o IFB soma só o que foi publicado desde a última execução
(`PncpSyncCheckpoint`) e **adiciona** ao total já acumulado
(`PncpContratacaoTotal`) — nunca consulta o PNCP em tempo real por
requisição de usuário; os usuários sempre leem o total pré-calculado
via `indicator_values`, como qualquer outro indicador do IFB.

**Duas modalidades acompanhadas**: "Pregão Eletrônico" (código 6, a
modalidade mais comum de contratação pública competitiva) e
"Dispensa" + "Inexigibilidade" (códigos 8 e 9, as duas formas de
contratação direta — sem licitação — previstas na Lei 14.133/2021).
Cada uma alimenta um indicador separado; a tabela já guarda
`modalidade_codigo` por linha, então as funções de leitura recebem
explicitamente quais códigos somar — nunca misturam licitação
competitiva com contratação direta no mesmo número.

Validado ao vivo: uma semana de janeiro/2026 (modalidade Pregão
Eletrônico) trouxe 2.530 registros reais, com valores individuais na
faixa de dezenas de milhares de reais (compatível com compras
municipais/estaduais de rotina) — nenhum valor inventado, cada
registro vem direto da API pública do PNCP.
"""
import time
from datetime import date, datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.pncp_accumulation import PncpContratacaoTotal, PncpSyncCheckpoint

BASE_URL = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"

REQUEST_HEADERS = {
    "User-Agent": "IFB-Sync/1.0 (+https://github.com/douglasoliveira21/ifb2)",
}
MAX_ATTEMPTS = 5
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
PAGE_SIZE = 50
# Pausa entre páginas — o PNCP aplica rate limit sob rajadas de
# requisições consecutivas (confirmado empiricamente: paginar sem
# pausa dispara 429 depois de ~8 páginas). Não é sobre "tempo real por
# usuário" (essa busca só roda no sync, nunca por requisição de
# usuário) — é só respeitar o limite da API mesmo dentro de um sync.
DELAY_BETWEEN_PAGES_SECONDS = 0.5

# Códigos da tabela de domínio de modalidade do PNCP (Lei 14.133/2021)
# — confirmados empiricamente contra a API real (campo `modalidadeNome`
# dos registros retornados: 6 = "Pregão - Eletrônico", 8 = "Dispensa",
# 9 = "Inexigibilidade").
MODALIDADE_PREGAO_ELETRONICO = 6
MODALIDADES_CONTRATACAO_DIRETA = [8, 9]
MODALIDADES_ACOMPANHADAS = [MODALIDADE_PREGAO_ELETRONICO, *MODALIDADES_CONTRATACAO_DIRETA]

# Não há registro publicado no PNCP anterior a 2021 (Lei 14.133/2021,
# que criou a obrigatoriedade de publicação).
PRIMEIRO_ANO_PNCP = 2021


def _get_with_retry(params: dict, *, timeout: float) -> dict:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = httpx.get(BASE_URL, params=params, headers=REQUEST_HEADERS, timeout=timeout)
        except httpx.TransportError:
            if attempt < MAX_ATTEMPTS:
                time.sleep(2 * attempt)
                continue
            raise
        if response.status_code in RETRY_STATUS_CODES and attempt < MAX_ATTEMPTS:
            time.sleep(3 * attempt)
            continue
        response.raise_for_status()
        return response.json()
    raise AssertionError("unreachable")


def fetch_contratacoes_publicadas(
    modalidade_codigo: int, data_inicial: date, data_final: date, *, timeout: float = 30.0
) -> list[dict]:
    """Busca todas as contratações publicadas no intervalo (inclusive),
    paginando até o fim. Cada item traz `unidadeOrgao.ufSigla`,
    `valorTotalEstimado` e `dataPublicacaoPncp`."""
    items: list[dict] = []
    pagina = 1
    while True:
        params = {
            "dataInicial": data_inicial.strftime("%Y%m%d"),
            "dataFinal": data_final.strftime("%Y%m%d"),
            "codigoModalidadeContratacao": modalidade_codigo,
            "pagina": pagina,
            "tamanhoPagina": PAGE_SIZE,
        }
        payload = _get_with_retry(params, timeout=timeout)
        items.extend(payload.get("data", []))
        total_paginas = payload.get("totalPaginas", 0)
        if pagina >= total_paginas:
            break
        pagina += 1
        time.sleep(DELAY_BETWEEN_PAGES_SECONDS)
    return items


def _aggregate_by_ano_uf(items: list[dict]) -> dict[tuple[int, str], float]:
    totals: dict[tuple[int, str], float] = {}
    for item in items:
        valor = item.get("valorTotalEstimado")
        if valor is None:
            continue
        data_publicacao = item.get("dataPublicacaoPncp")
        if not data_publicacao:
            continue
        ano = datetime.fromisoformat(data_publicacao).year
        uf = (item.get("unidadeOrgao") or {}).get("ufSigla")
        if not uf:
            continue
        key = (ano, uf)
        totals[key] = totals.get(key, 0.0) + float(valor)
    return totals


def _get_checkpoint(db: Session, modalidade_codigo: int) -> date:
    checkpoint = db.get(PncpSyncCheckpoint, modalidade_codigo)
    if checkpoint is not None:
        return checkpoint.ultima_data_final
    return date(PRIMEIRO_ANO_PNCP, 1, 1) - timedelta(days=1)


def _set_checkpoint(db: Session, modalidade_codigo: int, data_final: date) -> None:
    stmt = (
        pg_insert(PncpSyncCheckpoint)
        .values(modalidade_codigo=modalidade_codigo, ultima_data_final=data_final)
        .on_conflict_do_update(
            index_elements=["modalidade_codigo"],
            set_={"ultima_data_final": data_final},
        )
    )
    db.execute(stmt)


def _add_to_accumulated_totals(db: Session, modalidade_codigo: int, deltas: dict[tuple[int, str], float]) -> None:
    for (ano, uf), delta in deltas.items():
        stmt = (
            pg_insert(PncpContratacaoTotal)
            .values(ano=ano, uf=uf, modalidade_codigo=modalidade_codigo, valor_total=delta)
            .on_conflict_do_update(
                index_elements=["ano", "uf", "modalidade_codigo"],
                set_={"valor_total": PncpContratacaoTotal.valor_total + delta},
            )
        )
        db.execute(stmt)


def sync_pncp_incremental(db: Session, *, timeout: float = 30.0) -> None:
    """Busca só o que falta desde o último checkpoint de cada modalidade
    acompanhada, soma por ano/UF, e adiciona ao total já acumulado —
    nunca refaz a soma do histórico inteiro. Commita ao final de cada
    modalidade (uma falha numa modalidade não perde o progresso das
    demais)."""
    ontem = date.today() - timedelta(days=1)

    for modalidade_codigo in MODALIDADES_ACOMPANHADAS:
        checkpoint = _get_checkpoint(db, modalidade_codigo)
        data_inicial = checkpoint + timedelta(days=1)
        if data_inicial > ontem:
            continue  # já sincronizado até ontem, nada novo a buscar

        items = fetch_contratacoes_publicadas(modalidade_codigo, data_inicial, ontem, timeout=timeout)
        deltas = _aggregate_by_ano_uf(items)
        _add_to_accumulated_totals(db, modalidade_codigo, deltas)
        _set_checkpoint(db, modalidade_codigo, ontem)
        db.commit()


def read_accumulated_totals_by_state(
    db: Session, modalidade_codigos: list[int]
) -> dict[str, list[tuple[int, float]]]:
    """Lê os totais já acumulados (não faz nenhuma chamada HTTP), somando
    só as modalidades passadas — devolve {uf: [(ano, valor), ...]}."""
    rows = db.execute(
        select(
            PncpContratacaoTotal.ano,
            PncpContratacaoTotal.uf,
            PncpContratacaoTotal.valor_total,
        ).where(PncpContratacaoTotal.modalidade_codigo.in_(modalidade_codigos))
    ).all()

    by_state: dict[str, dict[int, float]] = {}
    for ano, uf, valor in rows:
        by_state.setdefault(uf, {})
        by_state[uf][ano] = by_state[uf].get(ano, 0.0) + float(valor)

    return {uf: sorted(anos.items()) for uf, anos in by_state.items()}


def read_accumulated_totals_brasil(db: Session, modalidade_codigos: list[int]) -> list[tuple[int, float]]:
    """Mesma leitura, somada para o Brasil."""
    rows = db.execute(
        select(PncpContratacaoTotal.ano, PncpContratacaoTotal.valor_total).where(
            PncpContratacaoTotal.modalidade_codigo.in_(modalidade_codigos)
        )
    ).all()

    by_year: dict[int, float] = {}
    for ano, valor in rows:
        by_year[ano] = by_year.get(ano, 0.0) + float(valor)

    return sorted(by_year.items())
