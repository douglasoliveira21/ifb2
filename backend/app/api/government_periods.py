from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.government_period import GovernmentLevel, GovernmentPeriod
from app.models.location import Location, LocationType
from app.schemas.indicator import GovernmentPeriodOut

router = APIRouter(prefix="/government-periods", tags=["government-periods"])


@router.get("", response_model=list[GovernmentPeriodOut])
def list_government_periods(location: str = "BR", db: Session = Depends(get_db)) -> list[GovernmentPeriodOut]:
    """Períodos de governo de uma localização — `BR` (padrão, nível
    federal) ou a sigla de um estado (nível estadual, ex: `?location=SP`).
    Datas de posse são registro histórico público, não estatística — ver
    `app/sync/seed_government_periods.py`."""
    code = location.upper()
    loc_type = LocationType.country if code == "BR" else LocationType.state
    level = GovernmentLevel.federal if code == "BR" else GovernmentLevel.state

    loc = db.execute(select(Location).where(Location.type == loc_type, Location.code == code)).scalar_one_or_none()
    if loc is None:
        return []

    rows = db.execute(
        select(GovernmentPeriod)
        .where(GovernmentPeriod.location_id == loc.id, GovernmentPeriod.level == level)
        .order_by(GovernmentPeriod.start_date)
    ).scalars().all()

    return [
        GovernmentPeriodOut(
            id=row.id,
            level=row.level.value,
            holder_name=row.holder_name,
            location_code=loc.code,
            start_date=row.start_date,
            end_date=row.end_date,
        )
        for row in rows
    ]
