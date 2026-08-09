from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.data_revision import DataRevision
from app.models.indicator_definition import IndicatorDefinition
from app.models.indicator_methodology import IndicatorMethodology
from app.models.indicator_value import IndicatorValue
from app.models.location import Location
from app.models.source import Source
from app.models.sync_run import SyncRun
from app.schemas.transparency import (
    TransparencyCorrectionOut,
    TransparencyErrorOut,
    TransparencyMethodologyOut,
    TransparencyOut,
    TransparencySourceOut,
    TransparencySyncOut,
)

router = APIRouter(prefix="/transparency", tags=["transparency"])


@router.get("", response_model=TransparencyOut)
def get_transparency(db: Session = Depends(get_db)) -> TransparencyOut:
    sources = db.execute(select(Source).order_by(Source.name)).scalars().all()

    last_sync_per_source: dict = {}
    for run, source_name in db.execute(
        select(SyncRun, Source.name).join(Source, Source.id == SyncRun.source_id).order_by(SyncRun.started_at.desc())
    ):
        if source_name not in last_sync_per_source:
            last_sync_per_source[source_name] = run

    errors = db.execute(
        select(SyncRun, Source.name)
        .join(Source, Source.id == SyncRun.source_id)
        .where(SyncRun.status == "error")
        .order_by(SyncRun.started_at.desc())
        .limit(20)
    ).all()

    corrections = db.execute(
        select(DataRevision, IndicatorValue, IndicatorDefinition, Location.code)
        .join(IndicatorValue, IndicatorValue.id == DataRevision.indicator_value_id)
        .join(IndicatorDefinition, IndicatorDefinition.id == IndicatorValue.indicator_id)
        .join(Location, Location.id == IndicatorValue.location_id)
        .where(DataRevision.changed_by != "sync")
        .order_by(DataRevision.changed_at.desc())
        .limit(20)
    ).all()

    methodologies = db.execute(
        select(IndicatorMethodology, IndicatorDefinition)
        .join(IndicatorDefinition, IndicatorDefinition.id == IndicatorMethodology.indicator_id)
        .order_by(IndicatorDefinition.name, IndicatorMethodology.version.desc())
    ).all()
    latest_methodology_per_indicator: dict = {}
    for methodology, definition in methodologies:
        if definition.slug not in latest_methodology_per_indicator:
            latest_methodology_per_indicator[definition.slug] = (methodology, definition)

    return TransparencyOut(
        sources=[
            TransparencySourceOut(name=s.name, url=s.url, description=s.description) for s in sources
        ],
        last_syncs=[
            TransparencySyncOut(
                source_name=name,
                status=run.status.value,
                finished_at=run.finished_at,
                records_processed=run.records_processed,
            )
            for name, run in last_sync_per_source.items()
        ],
        known_errors=[
            TransparencyErrorOut(source_name=name, started_at=run.started_at, error_message=run.error_message)
            for run, name in errors
        ],
        recent_corrections=[
            TransparencyCorrectionOut(
                indicator_slug=definition.slug,
                indicator_name=definition.name,
                location_code=code,
                reference_date=value.reference_date,
                previous_value=float(revision.previous_value),
                new_value=float(revision.new_value),
                reason=revision.reason,
                changed_at=revision.changed_at,
            )
            for revision, value, definition, code in corrections
        ],
        methodologies=[
            TransparencyMethodologyOut(
                indicator_slug=definition.slug,
                indicator_name=definition.name,
                version=methodology.version,
                published_at=methodology.published_at,
            )
            for methodology, definition in latest_methodology_per_indicator.values()
        ],
    )
