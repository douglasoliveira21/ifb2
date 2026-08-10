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
from app.sync.definitions import DEFORESTATION_LEGAL_AMAZON, INDICATORS, IndicatorSpec, StaticIndicatorMeta
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


def sync_prodes_states() -> None:
    by_state = fetch_prodes_by_state()
    for uf, points in by_state.items():
        sync_indicator(
            DEFORESTATION_LEGAL_AMAZON,
            fetch_points=lambda points=points: points,
            get_location=lambda db, uf=uf: get_state(db, uf),
        )


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
    refresh_summary_view()
    print("Materialized view `indicators` atualizada.")


if __name__ == "__main__":
    main()
