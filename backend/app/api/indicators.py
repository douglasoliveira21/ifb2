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


def _resolve_location(db: Session, location: str | None) -> Location | None:
    """`location` é `None`/"BR" para o Brasil (padrão), a sigla de um
    estado (2 letras) ou o código IBGE de 7 dígitos de um município —
    mesma convenção já usada em `app/api/compare.py` e
    `app/api/municipios.py`."""
    if location is None or location.upper() == "BR":
        return db.execute(select(Location).where(Location.type == LocationType.country)).scalar_one_or_none()

    code = location.upper()
    if len(code) == 2 and code.isalpha():
        return db.execute(
            select(Location).where(Location.type == LocationType.state, Location.code == code)
        ).scalar_one_or_none()

    return db.execute(
        select(Location).where(Location.type == LocationType.municipality, Location.code == location)
    ).scalar_one_or_none()


@router.get("/{slug}", response_model=IndicatorDetailOut)
def get_indicator(slug: str, location: str | None = None, db: Session = Depends(get_db)) -> IndicatorDetailOut:
    definition = db.execute(
        select(IndicatorDefinition).where(IndicatorDefinition.slug == slug)
    ).scalar_one_or_none()
    if definition is None or not definition.enabled:
        raise HTTPException(status_code=404, detail="Indicador não encontrado")

    resolved_location = _resolve_location(db, location)
    if resolved_location is None and location is not None:
        # `location` foi informado mas não corresponde a nenhum estado/
        # município conhecido — diferente de "location válida mas sem
        # dado sincronizado para este indicador" (esse caso cai no ramo
        # abaixo e devolve history/summary vazios, não 404).
        raise HTTPException(status_code=404, detail="Localização não encontrada")

    summary_row = None
    history: list[IndicatorValuePoint] = []
    if resolved_location is not None:
        summary_row = db.execute(
            select(indicator_summary).where(
                indicator_summary.c.indicator_id == definition.id,
                indicator_summary.c.location_id == resolved_location.id,
            )
        ).mappings().first()

        history_rows = db.execute(
            select(IndicatorValue)
            .where(
                IndicatorValue.indicator_id == definition.id,
                IndicatorValue.location_id == resolved_location.id,
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
