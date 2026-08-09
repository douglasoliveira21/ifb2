from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.indicator_definition import IndicatorDefinition
from app.models.indicator_methodology import IndicatorMethodology
from app.models.indicator_summary import indicator_summary
from app.models.indicator_value import IndicatorValue
from app.models.location import Location, LocationType
from app.schemas.indicator import IndicatorDetailOut, IndicatorSummaryOut, IndicatorValuePoint

router = APIRouter(prefix="/indicators", tags=["indicators"])


@router.get("", response_model=list[IndicatorSummaryOut])
def list_indicators(db: Session = Depends(get_db)) -> list[IndicatorSummaryOut]:
    country = db.execute(select(Location).where(Location.type == LocationType.country)).scalar_one_or_none()
    if country is None:
        return []
    rows = db.execute(
        select(indicator_summary).where(indicator_summary.c.location_id == country.id)
    ).mappings().all()
    return [IndicatorSummaryOut.model_validate(dict(row)) for row in rows]


@router.get("/{slug}", response_model=IndicatorDetailOut)
def get_indicator(slug: str, db: Session = Depends(get_db)) -> IndicatorDetailOut:
    definition = db.execute(
        select(IndicatorDefinition).where(IndicatorDefinition.slug == slug)
    ).scalar_one_or_none()
    if definition is None or not definition.enabled:
        raise HTTPException(status_code=404, detail="Indicador não encontrado")

    country = db.execute(select(Location).where(Location.type == LocationType.country)).scalar_one_or_none()

    summary_row = None
    history: list[IndicatorValuePoint] = []
    if country is not None:
        summary_row = db.execute(
            select(indicator_summary).where(
                indicator_summary.c.indicator_id == definition.id,
                indicator_summary.c.location_id == country.id,
            )
        ).mappings().first()

        history_rows = db.execute(
            select(IndicatorValue)
            .where(
                IndicatorValue.indicator_id == definition.id,
                IndicatorValue.location_id == country.id,
                IndicatorValue.is_revised == False,  # noqa: E712
            )
            .order_by(IndicatorValue.reference_date)
        ).scalars().all()
        history = [IndicatorValuePoint.model_validate(row) for row in history_rows]

    methodology_row = db.execute(
        select(IndicatorMethodology)
        .where(IndicatorMethodology.indicator_id == definition.id)
        .order_by(IndicatorMethodology.version.desc())
    ).scalars().first()

    values = [point.value for point in history]

    return IndicatorDetailOut(
        slug=definition.slug,
        name=definition.name,
        category=definition.category.value,
        unit=definition.unit,
        polarity=definition.polarity.value,
        description_what=definition.description_what,
        description_how=definition.description_how,
        update_frequency=definition.update_frequency,
        source_name=definition.source.name,
        source_url=definition.source.url,
        methodology=methodology_row.content if methodology_row else None,
        summary=IndicatorSummaryOut.model_validate(dict(summary_row)) if summary_row else None,
        min_value=min(values) if values else None,
        max_value=max(values) if values else None,
        avg_value=sum(values) / len(values) if values else None,
        history=history,
    )
