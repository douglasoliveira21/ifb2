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
    DIVIDA_CONSOLIDADA_LIQUIDA_ESTADUAL,
    ESPERANCA_VIDA,
    ESPERANCA_VIDA_QUERY,
    IDEB_ANOS_FINAIS,
    IDEB_ANOS_INICIAIS,
    IDEB_ENSINO_MEDIO,
    IDEB_ZIP_URL,
    INDICATORS,
    LEITOS_SUS_ESTADUAL,
    MORTALIDADE_INFANTIL,
    MORTALIDADE_INFANTIL_QUERY,
    PIB_PER_CAPITA,
    PIB_PER_CAPITA_QUERY,
    RECEITA_TOTAL_REALIZADA_ESTADUAL,
    TAXA_ESCOLARIZACAO_6_A_14,
    TAXA_ESCOLARIZACAO_6_A_14_QUERY,
    TAXA_ESCOLARIZACAO_15_A_17,
    TAXA_ESCOLARIZACAO_15_A_17_QUERY,
    TAXA_MORTES_VIOLENTAS_INTENCIONAIS_ESTADUAL,
    TRANSFERENCIAS_CONSTITUCIONAIS_ESTADUAL,
    TRANSFERENCIAS_CONSTITUCIONAIS_MUNICIPAL,
    IndicatorSpec,
    StaticIndicatorMeta,
)
from app.sync.fbsp_client import fetch_mvi_rate_brasil, fetch_mvi_rate_by_state
from app.sync.ibge_client import (
    drop_future_years,
    drop_future_years_by_state,
    fetch_sidra_series,
    fetch_sidra_series_by_state,
)
from app.sync.inep_client import IdebSheetSpec, fetch_ideb_series
from app.sync.inpe_client import fetch_prodes_by_state, fetch_prodes_legal_amazon
from app.sync.leitos_sus_client import fetch_leitos_sus_brasil, fetch_leitos_sus_by_state
from app.sync.seed_government_periods import seed as seed_government_periods
from app.sync.seed_municipios import seed as seed_municipios
from app.sync.seed_states import seed as seed_states
from app.sync.siconfi_client import (
    DESPESA_COM_PESSOAL_RCL,
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


def main() -> None:
    seed_states()
    seed_municipios()
    seed_government_periods()
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
    # PIB per capita (tabela 6784) não tem quebra por estado no SIDRA.

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

    refresh_summary_view()
    print("Materialized view `indicators` atualizada.")


if __name__ == "__main__":
    main()
