from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.government_period import GovernmentLevel, GovernmentPeriod
from app.models.location import Location, LocationType
from app.schemas.indicator import GovernmentPeriodOut

router = APIRouter(prefix="/government-periods", tags=["government-periods"])


@router.get("", response_model=list[GovernmentPeriodOut])
def list_federal_periods(db: Session = Depends(get_db)) -> list[GovernmentPeriodOut]:
    country = db.execute(select(Location).where(Location.type == LocationType.country)).scalar_one_or_none()
    if country is None:
        return []

    rows = db.execute(
        select(GovernmentPeriod)
        .where(
            GovernmentPeriod.location_id == country.id,
            GovernmentPeriod.level == GovernmentLevel.federal,
        )
        .order_by(GovernmentPeriod.start_date)
    ).scalars().all()

    return [GovernmentPeriodOut.model_validate(row) for row in rows]
