from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.indicator_summary import indicator_summary
from app.models.location import Location, LocationType
from app.schemas.ranking import RankingDetailOut, RankingEntryOut, RankingListItemOut

router = APIRouter(prefix="/rankings", tags=["rankings"])

MIN_STATES_FOR_RANKING = 2


def _state_rows_by_indicator(db: Session) -> dict[str, list[dict]]:
    """Linhas da view `indicators` para localizações do tipo estado, com
    valor inicial e final presentes (sem isso não há o que ranquear),
    agrupadas por slug do indicador."""
    states = {
        loc.id: loc
        for loc in db.execute(select(Location).where(Location.type == LocationType.state)).scalars()
    }

    rows = db.execute(
        select(indicator_summary).where(indicator_summary.c.location_id.in_(states.keys()))
    ).mappings().all()

    by_indicator: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if row["first_value"] is None or row["last_value"] is None:
            continue
        if row["polarity"] == "neutral":
            continue  # sem direção de "melhora", não faz sentido ranquear
        state = states[row["location_id"]]
        by_indicator[row["slug"]].append({**row, "state": state})

    return by_indicator


def _sort_entries(rows: list[dict], polarity: str) -> list[dict]:
    reverse = polarity == "higher_is_better"
    return sorted(rows, key=lambda r: float(r["change_absolute"]), reverse=reverse)


@router.get("", response_model=list[RankingListItemOut])
def list_rankings(db: Session = Depends(get_db)) -> list[RankingListItemOut]:
    by_indicator = _state_rows_by_indicator(db)

    result: list[RankingListItemOut] = []
    for slug, rows in by_indicator.items():
        if len(rows) < MIN_STATES_FOR_RANKING:
            continue
        sample = rows[0]
        last_dates = [r["last_date"] for r in rows if r["last_date"] is not None]
        result.append(
            RankingListItemOut(
                slug=slug,
                indicator_name=sample["name"],
                category=sample["category"],
                unit=sample["unit"],
                polarity=sample["polarity"],
                states_count=len(rows),
                last_updated=max(last_dates) if last_dates else None,
            )
        )
    return sorted(result, key=lambda r: r.indicator_name)


@router.get("/{slug}", response_model=RankingDetailOut)
def get_ranking(slug: str, db: Session = Depends(get_db)) -> RankingDetailOut:
    by_indicator = _state_rows_by_indicator(db)
    rows = by_indicator.get(slug)
    if not rows or len(rows) < MIN_STATES_FOR_RANKING:
        raise HTTPException(status_code=404, detail="Ranking não encontrado")

    sample = rows[0]
    ordered = _sort_entries(rows, sample["polarity"])

    entries = [
        RankingEntryOut(
            rank=i + 1,
            state_code=r["state"].code,
            state_name=r["state"].name,
            first_value=float(r["first_value"]),
            last_value=float(r["last_value"]),
            change_absolute=float(r["change_absolute"]),
            classification=r["classification"],
            first_date=r["first_date"],
            last_date=r["last_date"],
        )
        for i, r in enumerate(ordered)
    ]

    return RankingDetailOut(
        slug=slug,
        indicator_name=sample["name"],
        category=sample["category"],
        unit=sample["unit"],
        polarity=sample["polarity"],
        entries=entries,
    )
