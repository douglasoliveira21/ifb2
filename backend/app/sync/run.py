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
    ESPERANCA_VIDA,
    ESPERANCA_VIDA_QUERY,
    IDEB_ANOS_FINAIS,
    IDEB_ANOS_INICIAIS,
    IDEB_ENSINO_MEDIO,
    IDEB_ZIP_URL,
    INDICATORS,
    MORTALIDADE_INFANTIL,
    MORTALIDADE_INFANTIL_QUERY,
    PIB_PER_CAPITA,
    PIB_PER_CAPITA_QUERY,
    IndicatorSpec,
    StaticIndicatorMeta,
)
from app.sync.ibge_client import (
    drop_future_years,
    drop_future_years_by_state,
    fetch_sidra_series,
    fetch_sidra_series_by_state,
)
from app.sync.inep_client import IdebSheetSpec, fetch_ideb_series
from app.sync.inpe_client import fetch_prodes_by_state, fetch_prodes_legal_amazon
from app.sync.seed_government_periods import seed as seed_government_periods
from app.sync.seed_states import seed as seed_states
from app.sync.upsert import (
    ensure_methodology,
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


def sync_prodes_states() -> None:
    sync_by_state(DEFORESTATION_LEGAL_AMAZON, fetch_prodes_by_state)


def refresh_summary_view() -> None:
    with engine.connect() as conn:
        conn.exec_driver_sql("REFRESH MATERIALIZED VIEW indicators")
        conn.commit()


def main() -> None:
    seed_government_periods()
    seed_states()
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

    refresh_summary_view()
    print("Materialized view `indicators` atualizada.")


if __name__ == "__main__":
    main()
