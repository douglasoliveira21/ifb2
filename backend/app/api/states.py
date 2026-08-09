from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.indicator_summary import indicator_summary
from app.models.location import Location, LocationType
from app.schemas.indicator import IndicatorSummaryOut
from app.schemas.state import StateDetailOut, StateSummaryOut

router = APIRouter(prefix="/states", tags=["states"])


@router.get("", response_model=list[StateSummaryOut])
def list_states(db: Session = Depends(get_db)) -> list[StateSummaryOut]:
    states = db.execute(
        select(Location).where(Location.type == LocationType.state).order_by(Location.name)
    ).scalars().all()

    result: list[StateSummaryOut] = []
    for state in states:
        rows = db.execute(
            select(indicator_summary).where(indicator_summary.c.location_id == state.id)
        ).mappings().all()

        last_dates = [row["last_date"] for row in rows if row["last_date"] is not None]
        result.append(
            StateSummaryOut(
                code=state.code,
                name=state.name,
                indicators_available=len(rows),
                melhoraram=sum(1 for row in rows if row["classification"] == "MELHOROU"),
                pioraram=sum(1 for row in rows if row["classification"] == "PIOROU"),
                last_updated=max(last_dates) if last_dates else None,
            )
        )
    return result


@router.get("/{uf}", response_model=StateDetailOut)
def get_state(uf: str, db: Session = Depends(get_db)) -> StateDetailOut:
    state = db.execute(
        select(Location).where(Location.type == LocationType.state, Location.code == uf.upper())
    ).scalar_one_or_none()
    if state is None:
        raise HTTPException(status_code=404, detail="Estado não encontrado")

    rows = db.execute(
        select(indicator_summary).where(indicator_summary.c.location_id == state.id)
    ).mappings().all()

    return StateDetailOut(
        code=state.code,
        name=state.name,
        indicators=[IndicatorSummaryOut.model_validate(dict(row)) for row in rows],
    )
