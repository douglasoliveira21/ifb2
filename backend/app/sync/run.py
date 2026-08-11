"""Orquestrador de sincronização.

Roda os conectores dos indicadores reais definidos em `app/sync/definitions.py`,
cada um isolado em sua própria sessão/transação: a falha de uma fonte não
impede as demais de sincronizar. Ao final, recalcula a materialized view
`indicators`.

Uso: python -m app.sync.run
"""
import sys
from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.db import SessionLocal, engine
from app.models.location import Location
from app.models.sync_run import SyncRun, SyncStatus
from app.sync.bcb_client import (
    SeriesPoint,
    fetch_daily_series_chunked,
    fetch_series,
    invert_sign,
    resample_to_month_end,
)
from app.sync.definitions import (
    ALFABETISMO,
    ALFABETISMO_QUERY,
    DEFORESTATION_LEGAL_AMAZON,
    DESPESA_COM_PESSOAL_ESTADUAL,
    DESPESA_COM_PESSOAL_MUNICIPAL,
    DESPESA_EDUCACAO_ESTADUAL,
    DESPESA_SAUDE_ESTADUAL,
    DIVIDA_CONSOLIDADA_LIQUIDA_ESTADUAL,
    DOMICILIOS_AGUA_REDE_GERAL,
    DOMICILIOS_AGUA_REDE_GERAL_QUERY,
    DOMICILIOS_ALUGADOS,
    DOMICILIOS_ALUGADOS_QUERY,
    DOMICILIOS_BOLSA_FAMILIA,
    DOMICILIOS_BOLSA_FAMILIA_QUERY,
    DOMICILIOS_COM_INTERNET,
    DOMICILIOS_COM_INTERNET_QUERY,
    DOMICILIOS_ENERGIA_ELETRICA,
    DOMICILIOS_ENERGIA_ELETRICA_QUERY,
    DOMICILIOS_ESGOTO_REDE_GERAL,
    DOMICILIOS_ESGOTO_REDE_GERAL_QUERY,
    DOMICILIOS_LIXO_COLETADO,
    DOMICILIOS_LIXO_COLETADO_QUERY,
    DOMICILIOS_SEM_DOCUMENTO_PROPRIEDADE,
    DOMICILIOS_SEM_DOCUMENTO_PROPRIEDADE_QUERY,
    ESCOLARIDADE_AVANCADA,
    ESCOLARIDADE_AVANCADA_QUERY,
    ESPERANCA_VIDA,
    ESPERANCA_VIDA_QUERY,
    EXPORTACOES_TOTAIS,
    IDEB_ANOS_FINAIS,
    IDEB_ANOS_INICIAIS,
    IDEB_ENSINO_MEDIO,
    IDEB_ZIP_URL,
    IMPORTACOES_TOTAIS,
    INDICATORS,
    INDICE_ENVELHECIMENTO,
    INDICE_ENVELHECIMENTO_QUERY,
    INDICE_GINI_PIB_MUNICIPAL,
    INDICE_GINI_PIB_MUNICIPAL_QUERY,
    INDICE_GINI_RENDA,
    INDICE_GINI_RENDA_QUERY,
    LEITOS_SUS_ESTADUAL,
    MEDIA_ANOS_ESTUDO,
    MEDIA_ANOS_ESTUDO_QUERY,
    MORTALIDADE_INFANTIL,
    MORTALIDADE_INFANTIL_QUERY,
    NIVEL_OCUPACAO,
    NIVEL_OCUPACAO_QUERY,
    OBITOS_CAUSAS_NAO_NATURAIS,
    OBITOS_CAUSAS_NAO_NATURAIS_QUERY,
    CRESCIMENTO_PIB,
    CRESCIMENTO_PIB_ADMINISTRACAO_PUBLICA,
    CRESCIMENTO_PIB_ADMINISTRACAO_PUBLICA_QUERY,
    CRESCIMENTO_PIB_AGROPECUARIO,
    CRESCIMENTO_PIB_AGROPECUARIO_QUERY,
    CRESCIMENTO_PIB_INDUSTRIAL,
    CRESCIMENTO_PIB_INDUSTRIAL_QUERY,
    CRESCIMENTO_PIB_QUERY,
    CRESCIMENTO_PIB_SERVICOS,
    CRESCIMENTO_PIB_SERVICOS_QUERY,
    NASCIMENTOS,
    NASCIMENTOS_QUERY,
    OBITOS,
    OBITOS_QUERY,
    PIB_DEFLATOR,
    PIB_DEFLATOR_QUERY,
    PIB_PER_CAPITA,
    PIB_PER_CAPITA_QUERY,
    PIB_VALORES_CORRENTES,
    PIB_VALORES_CORRENTES_QUERY,
    POPULACAO_RESIDENTE,
    POPULACAO_RESIDENTE_QUERY,
    PROCESSOS_AJUIZADOS_ESTADUAL,
    PRODUCAO_INDUSTRIAL,
    PRODUCAO_INDUSTRIAL_QUERY,
    RAZAO_DEPENDENCIA_IDOSOS,
    RAZAO_DEPENDENCIA_IDOSOS_QUERY,
    RAZAO_RENDIMENTO_MULHER_HOMEM,
    RECEITA_TOTAL_REALIZADA_ESTADUAL,
    RENDIMENTO_HOMENS_QUERY,
    RENDIMENTO_MULHERES_QUERY,
    TAXA_FREQUENCIA_PRE_ESCOLA,
    TAXA_FREQUENCIA_PRE_ESCOLA_QUERY,
    RENDIMENTO_MEDIO_ANUAL,
    RENDIMENTO_MEDIO_ANUAL_QUERY,
    TAXA_CRESCIMENTO_POPULACIONAL,
    TAXA_CRESCIMENTO_POPULACIONAL_QUERY,
    TAXA_DESOCUPACAO_ANUAL,
    TAXA_DESOCUPACAO_ANUAL_QUERY,
    TAXA_ESCOLARIZACAO_6_A_14,
    TAXA_ESCOLARIZACAO_6_A_14_QUERY,
    TAXA_ESCOLARIZACAO_15_A_17,
    TAXA_ESCOLARIZACAO_15_A_17_QUERY,
    TAXA_FECUNDIDADE,
    TAXA_FECUNDIDADE_QUERY,
    TAXA_INFORMALIDADE,
    TAXA_INFORMALIDADE_QUERY,
    TAXA_INVESTIMENTO,
    TAXA_INVESTIMENTO_QUERY,
    TAXA_MORTALIDADE_GERAL,
    TAXA_MORTALIDADE_GERAL_QUERY,
    TAXA_MORTES_VIOLENTAS_INTENCIONAIS_ESTADUAL,
    TAXA_NATALIDADE,
    TAXA_NATALIDADE_QUERY,
    TAXA_POUPANCA,
    TAXA_POUPANCA_QUERY,
    TRANSFERENCIAS_CONSTITUCIONAIS_ESTADUAL,
    TRANSFERENCIAS_CONSTITUCIONAIS_MUNICIPAL,
    VALOR_PRODUCAO_AGRICOLA,
    VALOR_PRODUCAO_AGRICOLA_QUERY,
    IndicatorSpec,
    StaticIndicatorMeta,
)
from app.sync.comexstat_client import fetch_totals_brasil as fetch_comex_totals_brasil
from app.sync.comexstat_client import fetch_totals_by_state as fetch_comex_totals_by_state
from app.sync.datajud_client import (
    fetch_processos_ajuizados_series_brasil,
    fetch_processos_ajuizados_series_by_state,
)
from app.sync.fbsp_client import fetch_mvi_rate_brasil, fetch_mvi_rate_by_state
from app.sync.ibge_client import (
    drop_future_years,
    drop_future_years_by_state,
    fetch_sidra_series,
    fetch_sidra_series_by_state,
    fetch_sidra_series_monthly,
    fetch_sidra_series_monthly_by_state,
    fetch_sidra_series_quarterly,
)
from app.sync.inep_client import IdebSheetSpec, fetch_ideb_series
from app.sync.inpe_client import fetch_prodes_by_state, fetch_prodes_legal_amazon
from app.sync.leitos_sus_client import fetch_leitos_sus_brasil, fetch_leitos_sus_by_state
from app.sync.seed_government_periods import seed as seed_government_periods
from app.sync.seed_municipios import seed as seed_municipios
from app.sync.seed_states import seed as seed_states
from app.sync.siconfi_client import (
    DESPESA_COM_PESSOAL_RCL,
    DESPESA_EDUCACAO_PERCENTUAL,
    DESPESA_SAUDE_PERCENTUAL,
    DIVIDA_CONSOLIDADA_LIQUIDA_RCL,
    fetch_rgf_by_municipio,
    fetch_rgf_by_state,
    fetch_rreo_by_state,
)
from app.sync.tesouro_transferencias_client import (
    fetch_transferencias_constitucionais_by_municipio,
    fetch_transferencias_constitucionais_by_state,
)
from app.sync.upsert import (
    ensure_methodology,
    get_municipio,
    get_or_create_brasil,
    get_or_create_indicator_definition,
    get_or_create_source,
    get_state,
    upsert_indicator_values,
)

IndicatorMeta = IndicatorSpec | StaticIndicatorMeta


def _ratio_series(numerator: list[SeriesPoint], denominator: list[SeriesPoint]) -> list[SeriesPoint]:
    """Combina duas séries do SIDRA ponto a ponto (mesmo ano) em uma razão
    percentual — usado quando o indicador é uma comparação entre duas
    séries que o SIDRA não traz prontas (ex: rendimento mulher/homem)."""
    denom_by_date = {p.reference_date: p.value for p in denominator}
    points = []
    for p in numerator:
        denom = denom_by_date.get(p.reference_date)
        if denom:
            points.append(SeriesPoint(reference_date=p.reference_date, value=round(p.value / denom * 100, 1)))
    return points


def _ratio_series_by_state(
    numerator: dict[str, list[SeriesPoint]], denominator: dict[str, list[SeriesPoint]]
) -> dict[str, list[SeriesPoint]]:
    return {
        uf: _ratio_series(points, denominator[uf])
        for uf, points in numerator.items()
        if uf in denominator
    }


def sync_indicator(
    meta: IndicatorMeta,
    fetch_points: Callable[[], list[SeriesPoint]],
    get_location: Callable[[Session], Location | None] = get_or_create_brasil,
) -> None:
    db = SessionLocal()
    started_at = datetime.now(timezone.utc)
    try:
        source = get_or_create_source(db, meta.source)
        location = get_location(db)
        if location is None:
            raise RuntimeError("localização não encontrada — rode o seed de estados antes do sync")

        definition = get_or_create_indicator_definition(db, meta, source)
        ensure_methodology(db, definition, meta.methodology)
        db.flush()

        points = fetch_points()

        processed = upsert_indicator_values(db, definition, location, source, points)

        db.add(
            SyncRun(
                source_id=source.id,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                status=SyncStatus.success,
                records_processed=processed,
            )
        )
        db.commit()
        print(f"[{meta.slug}/{location.code}] ok — {processed} ponto(s) processado(s).")
    except Exception as exc:  # noqa: BLE001 — falha de uma fonte não pode derrubar as demais
        db.rollback()
        error_db = SessionLocal()
        try:
            source = get_or_create_source(error_db, meta.source)
            error_db.add(
                SyncRun(
                    source_id=source.id,
                    started_at=started_at,
                    finished_at=datetime.now(timezone.utc),
                    status=SyncStatus.error,
                    records_processed=0,
                    error_message=str(exc)[:2000],
                )
            )
            error_db.commit()
        finally:
            error_db.close()
        print(f"[{meta.slug}] ERRO — {exc}", file=sys.stderr)
    finally:
        db.close()


def sync_bcb_indicator(spec: IndicatorSpec) -> None:
    def fetch_points() -> list[SeriesPoint]:
        # Séries diárias longas (marcadas por resample_monthly) precisam de
        # busca em blocos — a API do BCB recusa consulta sem filtro de data
        # em séries diárias com mais de 10 anos de histórico.
        if spec.resample_monthly:
            points = fetch_daily_series_chunked(spec.sgs_series_code)
            points = resample_to_month_end(points)
        else:
            points = fetch_series(spec.sgs_series_code)
        if spec.invert_sign:
            points = invert_sign(points)
        return points

    sync_indicator(spec, fetch_points)


def _log_fetch_error(meta: IndicatorMeta, started_at: datetime, exc: Exception) -> None:
    """Registra um SyncRun de erro quando a busca por-estado falha antes de
    chegar a processar qualquer UF — sem isso, a exceção nunca apareceria
    em `sync_runs` e a falha ficaria só no stderr."""
    db = SessionLocal()
    try:
        source = get_or_create_source(db, meta.source)
        db.add(
            SyncRun(
                source_id=source.id,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                status=SyncStatus.error,
                records_processed=0,
                error_message=str(exc)[:2000],
            )
        )
        db.commit()
    finally:
        db.close()
    print(f"[{meta.slug}/por-estado] ERRO — {exc}", file=sys.stderr)


def sync_by_state(
    meta: IndicatorMeta, fetch_by_state: Callable[[], dict[str, list[SeriesPoint]]]
) -> None:
    """Sincroniza o mesmo indicador para cada estado com dado disponível —
    usado para as séries que trazem as UFs de uma vez (INPE, SIDRA/IBGE).
    A busca em si é isolada: se falhar, vira um SyncRun de erro em vez de
    derrubar o restante da sincronização."""
    started_at = datetime.now(timezone.utc)
    try:
        by_state = fetch_by_state()
    except Exception as exc:  # noqa: BLE001 — mesma regra: uma fonte não derruba as demais
        _log_fetch_error(meta, started_at, exc)
        return

    for uf, points in by_state.items():
        sync_indicator(
            meta,
            fetch_points=lambda points=points: points,
            get_location=lambda db, uf=uf: get_state(db, uf),
        )


def sync_by_municipio(
    meta: IndicatorMeta, fetch_by_municipio: Callable[[], dict[str, list[SeriesPoint]]]
) -> None:
    """Mesmo padrão de `sync_by_state`, para os ~5.570 municípios. A busca
    HTTP already é paralela dentro de `fetch_by_municipio` (ver
    `tesouro_transferencias_client.py`/`siconfi_client.py`); a escrita no
    banco aqui continua sequencial, uma sessão por município — em ~5.570
    iterações isso é a parte mais lenta do sync municipal (minutos, não
    segundos), aceitável para um cron diário mas um candidato óbvio a
    otimizar (upsert em lote) se o volume de indicadores municipais
    crescer além deste piloto."""
    started_at = datetime.now(timezone.utc)
    try:
        by_municipio = fetch_by_municipio()
    except Exception as exc:  # noqa: BLE001 — mesma regra: uma fonte não derruba as demais
        _log_fetch_error(meta, started_at, exc)
        return

    for codigo, points in by_municipio.items():
        sync_indicator(
            meta,
            fetch_points=lambda points=points: points,
            get_location=lambda db, codigo=codigo: get_municipio(db, codigo),
        )


def sync_prodes_states() -> None:
    sync_by_state(DEFORESTATION_LEGAL_AMAZON, fetch_prodes_by_state)


def refresh_summary_view() -> None:
    with engine.connect() as conn:
        conn.exec_driver_sql("REFRESH MATERIALIZED VIEW indicators")
        conn.commit()


def _run_seed(name: str, seed_fn: Callable[[], None]) -> None:
    """Roda um seed isolado — se falhar (ex: migration ainda não aplicada
    no banco), loga e segue para os indicadores em vez de derrubar a sync
    inteira. Diferente dos indicadores (que isolam falha por SyncRun), os
    seeds não têm tabela própria de log — por enquanto só stderr."""
    try:
        seed_fn()
    except Exception as exc:  # noqa: BLE001 — mesma regra: uma falha não pode travar tudo
        print(f"[seed:{name}] ERRO — {exc}", file=sys.stderr)


def main() -> None:
    _run_seed("states", seed_states)
    _run_seed("municipios", seed_municipios)
    _run_seed("government_periods", seed_government_periods)
    for spec in INDICATORS:
        sync_bcb_indicator(spec)
    sync_indicator(DEFORESTATION_LEGAL_AMAZON, fetch_prodes_legal_amazon)
    sync_prodes_states()
    sync_indicator(ALFABETISMO, lambda: fetch_sidra_series(ALFABETISMO_QUERY))
    sync_by_state(ALFABETISMO, lambda: fetch_sidra_series_by_state(ALFABETISMO_QUERY))

    sync_indicator(ESPERANCA_VIDA, lambda: drop_future_years(fetch_sidra_series(ESPERANCA_VIDA_QUERY)))
    sync_by_state(
        ESPERANCA_VIDA,
        lambda: drop_future_years_by_state(fetch_sidra_series_by_state(ESPERANCA_VIDA_QUERY)),
    )

    sync_indicator(
        MORTALIDADE_INFANTIL, lambda: drop_future_years(fetch_sidra_series(MORTALIDADE_INFANTIL_QUERY))
    )
    sync_by_state(
        MORTALIDADE_INFANTIL,
        lambda: drop_future_years_by_state(fetch_sidra_series_by_state(MORTALIDADE_INFANTIL_QUERY)),
    )

    sync_indicator(PIB_PER_CAPITA, lambda: fetch_sidra_series(PIB_PER_CAPITA_QUERY))
    sync_indicator(PIB_VALORES_CORRENTES, lambda: fetch_sidra_series(PIB_VALORES_CORRENTES_QUERY))
    sync_indicator(CRESCIMENTO_PIB, lambda: fetch_sidra_series(CRESCIMENTO_PIB_QUERY))
    sync_indicator(PIB_DEFLATOR, lambda: fetch_sidra_series(PIB_DEFLATOR_QUERY))
    # Tabela 6784 (Contas Nacionais Anuais) não tem quebra por estado no SIDRA.

    for meta, query in [
        (CRESCIMENTO_PIB_AGROPECUARIO, CRESCIMENTO_PIB_AGROPECUARIO_QUERY),
        (CRESCIMENTO_PIB_INDUSTRIAL, CRESCIMENTO_PIB_INDUSTRIAL_QUERY),
        (CRESCIMENTO_PIB_SERVICOS, CRESCIMENTO_PIB_SERVICOS_QUERY),
        (CRESCIMENTO_PIB_ADMINISTRACAO_PUBLICA, CRESCIMENTO_PIB_ADMINISTRACAO_PUBLICA_QUERY),
        (TAXA_INVESTIMENTO, TAXA_INVESTIMENTO_QUERY),
        (TAXA_POUPANCA, TAXA_POUPANCA_QUERY),
    ]:
        sync_indicator(meta, lambda query=query: fetch_sidra_series_quarterly(query))
    # Tabelas 5932/6726/6727 (Contas Nacionais Trimestrais) não têm quebra por estado no SIDRA.

    sync_indicator(PRODUCAO_INDUSTRIAL, lambda: fetch_sidra_series_monthly(PRODUCAO_INDUSTRIAL_QUERY))
    sync_by_state(PRODUCAO_INDUSTRIAL, lambda: fetch_sidra_series_monthly_by_state(PRODUCAO_INDUSTRIAL_QUERY))

    sync_indicator(POPULACAO_RESIDENTE, lambda: fetch_sidra_series(POPULACAO_RESIDENTE_QUERY))
    sync_by_state(POPULACAO_RESIDENTE, lambda: fetch_sidra_series_by_state(POPULACAO_RESIDENTE_QUERY))

    for meta, query in [
        (NASCIMENTOS, NASCIMENTOS_QUERY),
        (OBITOS, OBITOS_QUERY),
        (TAXA_CRESCIMENTO_POPULACIONAL, TAXA_CRESCIMENTO_POPULACIONAL_QUERY),
        (TAXA_NATALIDADE, TAXA_NATALIDADE_QUERY),
        (TAXA_MORTALIDADE_GERAL, TAXA_MORTALIDADE_GERAL_QUERY),
        (TAXA_FECUNDIDADE, TAXA_FECUNDIDADE_QUERY),
        (INDICE_ENVELHECIMENTO, INDICE_ENVELHECIMENTO_QUERY),
        (RAZAO_DEPENDENCIA_IDOSOS, RAZAO_DEPENDENCIA_IDOSOS_QUERY),
    ]:
        sync_indicator(meta, lambda query=query: drop_future_years(fetch_sidra_series(query)))
        sync_by_state(meta, lambda query=query: drop_future_years_by_state(fetch_sidra_series_by_state(query)))

    for meta, query in [
        (TAXA_DESOCUPACAO_ANUAL, TAXA_DESOCUPACAO_ANUAL_QUERY),
        (NIVEL_OCUPACAO, NIVEL_OCUPACAO_QUERY),
        (RENDIMENTO_MEDIO_ANUAL, RENDIMENTO_MEDIO_ANUAL_QUERY),
        (TAXA_INFORMALIDADE, TAXA_INFORMALIDADE_QUERY),
        (INDICE_GINI_RENDA, INDICE_GINI_RENDA_QUERY),
    ]:
        sync_indicator(meta, lambda query=query: drop_future_years(fetch_sidra_series(query)))
        sync_by_state(meta, lambda query=query: drop_future_years_by_state(fetch_sidra_series_by_state(query)))

    sync_indicator(
        OBITOS_CAUSAS_NAO_NATURAIS, lambda: drop_future_years(fetch_sidra_series(OBITOS_CAUSAS_NAO_NATURAIS_QUERY))
    )
    sync_by_state(
        OBITOS_CAUSAS_NAO_NATURAIS,
        lambda: drop_future_years_by_state(fetch_sidra_series_by_state(OBITOS_CAUSAS_NAO_NATURAIS_QUERY)),
    )

    sync_indicator(
        TAXA_ESCOLARIZACAO_6_A_14, lambda: fetch_sidra_series(TAXA_ESCOLARIZACAO_6_A_14_QUERY)
    )
    sync_by_state(
        TAXA_ESCOLARIZACAO_6_A_14,
        lambda: fetch_sidra_series_by_state(TAXA_ESCOLARIZACAO_6_A_14_QUERY),
    )

    sync_indicator(
        TAXA_ESCOLARIZACAO_15_A_17, lambda: fetch_sidra_series(TAXA_ESCOLARIZACAO_15_A_17_QUERY)
    )
    sync_by_state(
        TAXA_ESCOLARIZACAO_15_A_17,
        lambda: fetch_sidra_series_by_state(TAXA_ESCOLARIZACAO_15_A_17_QUERY),
    )

    for meta, query in [
        (MEDIA_ANOS_ESTUDO, MEDIA_ANOS_ESTUDO_QUERY),
        (ESCOLARIDADE_AVANCADA, ESCOLARIDADE_AVANCADA_QUERY),
        (DOMICILIOS_ALUGADOS, DOMICILIOS_ALUGADOS_QUERY),
        (DOMICILIOS_SEM_DOCUMENTO_PROPRIEDADE, DOMICILIOS_SEM_DOCUMENTO_PROPRIEDADE_QUERY),
        (DOMICILIOS_AGUA_REDE_GERAL, DOMICILIOS_AGUA_REDE_GERAL_QUERY),
        (DOMICILIOS_ESGOTO_REDE_GERAL, DOMICILIOS_ESGOTO_REDE_GERAL_QUERY),
        (DOMICILIOS_LIXO_COLETADO, DOMICILIOS_LIXO_COLETADO_QUERY),
        (DOMICILIOS_ENERGIA_ELETRICA, DOMICILIOS_ENERGIA_ELETRICA_QUERY),
        (DOMICILIOS_COM_INTERNET, DOMICILIOS_COM_INTERNET_QUERY),
        (DOMICILIOS_BOLSA_FAMILIA, DOMICILIOS_BOLSA_FAMILIA_QUERY),
    ]:
        sync_indicator(meta, lambda query=query: drop_future_years(fetch_sidra_series(query)))
        sync_by_state(meta, lambda query=query: drop_future_years_by_state(fetch_sidra_series_by_state(query)))

    sync_indicator(
        RAZAO_RENDIMENTO_MULHER_HOMEM,
        lambda: _ratio_series(
            fetch_sidra_series(RENDIMENTO_MULHERES_QUERY), fetch_sidra_series(RENDIMENTO_HOMENS_QUERY)
        ),
    )
    sync_by_state(
        RAZAO_RENDIMENTO_MULHER_HOMEM,
        lambda: _ratio_series_by_state(
            fetch_sidra_series_by_state(RENDIMENTO_MULHERES_QUERY),
            fetch_sidra_series_by_state(RENDIMENTO_HOMENS_QUERY),
        ),
    )

    sync_indicator(
        TAXA_FREQUENCIA_PRE_ESCOLA, lambda: fetch_sidra_series(TAXA_FREQUENCIA_PRE_ESCOLA_QUERY)
    )
    # Tabela 7140 não tem quebra por estado no SIDRA (só Brasil e Grandes Regiões).

    sync_indicator(
        IDEB_ANOS_INICIAIS,
        lambda: fetch_ideb_series(IdebSheetSpec(IDEB_ZIP_URL, "Brasil (Anos Iniciais)")),
    )
    sync_indicator(
        IDEB_ANOS_FINAIS,
        lambda: fetch_ideb_series(IdebSheetSpec(IDEB_ZIP_URL, "Brasil (Anos Finais)")),
    )
    sync_indicator(
        IDEB_ENSINO_MEDIO,
        lambda: fetch_ideb_series(IdebSheetSpec(IDEB_ZIP_URL, "Brasil (EM)")),
    )
    # IDEB não tem quebra por estado nesta planilha de divulgação nacional.

    sync_by_state(
        DIVIDA_CONSOLIDADA_LIQUIDA_ESTADUAL,
        lambda: fetch_rgf_by_state(DIVIDA_CONSOLIDADA_LIQUIDA_RCL),
    )
    sync_by_state(
        DESPESA_COM_PESSOAL_ESTADUAL,
        lambda: fetch_rgf_by_state(DESPESA_COM_PESSOAL_RCL),
    )
    # Ambos só têm dado por estado (RGF é declarado por ente federativo) —
    # não existe uma agregação "Brasil" oficial para dívida/pessoal estadual.

    sync_by_state(
        TRANSFERENCIAS_CONSTITUCIONAIS_ESTADUAL,
        fetch_transferencias_constitucionais_by_state,
    )
    sync_by_state(RECEITA_TOTAL_REALIZADA_ESTADUAL, fetch_rreo_by_state)
    sync_by_state(
        DESPESA_EDUCACAO_ESTADUAL, lambda: fetch_rreo_by_state(DESPESA_EDUCACAO_PERCENTUAL)
    )
    sync_by_state(
        DESPESA_SAUDE_ESTADUAL, lambda: fetch_rreo_by_state(DESPESA_SAUDE_PERCENTUAL)
    )
    # Ambos só têm dado por estado (RREO é declarado por ente federativo) —
    # não existe uma agregação "Brasil" oficial para despesa por função.

    sync_indicator(LEITOS_SUS_ESTADUAL, fetch_leitos_sus_brasil)
    sync_by_state(LEITOS_SUS_ESTADUAL, fetch_leitos_sus_by_state)

    sync_indicator(TAXA_MORTES_VIOLENTAS_INTENCIONAIS_ESTADUAL, fetch_mvi_rate_brasil)
    sync_by_state(TAXA_MORTES_VIOLENTAS_INTENCIONAIS_ESTADUAL, fetch_mvi_rate_by_state)
    # Fonte não-governamental (FBSP) — ver metodologia do indicador.

    # Piloto de granularidade municipal — seed_municipios() já rodou no
    # início de main(). Só o último ano completo por indicador (ver
    # metodologia de cada um) — não histórico completo, dado o volume.
    sync_by_municipio(
        TRANSFERENCIAS_CONSTITUCIONAIS_MUNICIPAL,
        fetch_transferencias_constitucionais_by_municipio,
    )
    sync_by_municipio(
        DESPESA_COM_PESSOAL_MUNICIPAL,
        lambda: fetch_rgf_by_municipio(DESPESA_COM_PESSOAL_RCL),
    )

    # Só a partir de 1994 (Plano Real) — antes disso a série troca de moeda
    # várias vezes (Cruzeiro, Cruzado, Cruzado Novo, Cruzeiro Real), ver
    # metodologia do indicador.
    sync_indicator(
        VALOR_PRODUCAO_AGRICOLA,
        lambda: [p for p in fetch_sidra_series(VALOR_PRODUCAO_AGRICOLA_QUERY) if p.reference_date.year >= 1994],
    )
    sync_by_state(
        VALOR_PRODUCAO_AGRICOLA,
        lambda: {
            uf: [p for p in points if p.reference_date.year >= 1994]
            for uf, points in fetch_sidra_series_by_state(VALOR_PRODUCAO_AGRICOLA_QUERY).items()
        },
    )

    sync_indicator(INDICE_GINI_PIB_MUNICIPAL, lambda: fetch_sidra_series(INDICE_GINI_PIB_MUNICIPAL_QUERY))
    sync_by_state(
        INDICE_GINI_PIB_MUNICIPAL, lambda: fetch_sidra_series_by_state(INDICE_GINI_PIB_MUNICIPAL_QUERY)
    )

    # Só até o último ano completo — o ano corrente teria contagem parcial
    # (o ano ainda não acabou) e pareceria uma queda de processos que não
    # é real, só um efeito de o ano estar em andamento.
    _last_complete_year = datetime.now(timezone.utc).year - 1
    sync_indicator(
        PROCESSOS_AJUIZADOS_ESTADUAL,
        lambda: fetch_processos_ajuizados_series_brasil(start_year=2019, end_year=_last_complete_year),
    )
    sync_by_state(
        PROCESSOS_AJUIZADOS_ESTADUAL,
        lambda: fetch_processos_ajuizados_series_by_state(start_year=2019, end_year=_last_complete_year),
    )

    sync_indicator(
        EXPORTACOES_TOTAIS,
        lambda: fetch_comex_totals_brasil("export", start_year=2015, end_year=_last_complete_year),
    )
    sync_by_state(
        EXPORTACOES_TOTAIS,
        lambda: fetch_comex_totals_by_state("export", start_year=2015, end_year=_last_complete_year),
    )
    sync_indicator(
        IMPORTACOES_TOTAIS,
        lambda: fetch_comex_totals_brasil("import", start_year=2015, end_year=_last_complete_year),
    )
    sync_by_state(
        IMPORTACOES_TOTAIS,
        lambda: fetch_comex_totals_by_state("import", start_year=2015, end_year=_last_complete_year),
    )

    refresh_summary_view()
    print("Materialized view `indicators` atualizada.")


if __name__ == "__main__":
    main()
