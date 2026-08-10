from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.indicator_definition import IndicatorDefinition
from app.models.indicator_value import IndicatorValue
from app.models.location import Location, LocationType
from app.schemas.compare import CompareIndicatorOut
from app.schemas.indicator import IndicatorValuePoint

router = APIRouter(prefix="/compare", tags=["compare"])


@router.get("/indicators", response_model=list[CompareIndicatorOut])
def compare_indicators(location: str = "BR", db: Session = Depends(get_db)) -> list[CompareIndicatorOut]:
    """Histórico completo dos indicadores habilitados de uma localização —
    `BR` (padrão, nacional) ou a sigla de um estado. Usado pelo comparador
    de períodos e pela Ficha por Governante, que calculam os valores de
    qualquer intervalo diretamente no frontend a partir da série completa."""
    code = location.upper()
    loc_type = LocationType.country if code == "BR" else LocationType.state

    loc = db.execute(select(Location).where(Location.type == loc_type, Location.code == code)).scalar_one_or_none()
    if loc is None:
        return []

    definitions = db.execute(
        select(IndicatorDefinition).where(IndicatorDefinition.enabled == True)  # noqa: E712
    ).scalars().all()

    result: list[CompareIndicatorOut] = []
    for definition in definitions:
        history_rows = db.execute(
            select(IndicatorValue)
            .where(
                IndicatorValue.indicator_id == definition.id,
                IndicatorValue.location_id == loc.id,
                IndicatorValue.is_revised == False,  # noqa: E712
            )
            .order_by(IndicatorValue.reference_date)
        ).scalars().all()

        if not history_rows:
            continue

        result.append(
            CompareIndicatorOut(
                slug=definition.slug,
                name=definition.name,
                category=definition.category.value,
                unit=definition.unit,
                polarity=definition.polarity.value,
                history=[IndicatorValuePoint.model_validate(row) for row in history_rows],
            )
        )
    return result
