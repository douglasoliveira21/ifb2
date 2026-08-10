from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.indicator_summary import indicator_summary
from app.models.location import Location, LocationType
from app.schemas.indicator import IndicatorSummaryOut
from app.schemas.municipio import MunicipioDetailOut, MunicipioSummaryOut
from app.sync.ibge_client import IBGE_UF_CODES

router = APIRouter(prefix="/municipios", tags=["municipios"])

_UF_TO_IBGE_CODE = {uf: codigo for codigo, uf in IBGE_UF_CODES.items()}


@router.get("/{uf}", response_model=list[MunicipioSummaryOut])
def list_municipios(uf: str, db: Session = Depends(get_db)) -> list[MunicipioSummaryOut]:
    """Municípios de um estado com indicador municipal disponível — só
    aparecem aqui municípios com pelo menos um indicador sincronizado (ver
    `app/sync/run.py:sync_by_municipio`), nunca os ~5.570 de uma vez."""
    codigo_uf = _UF_TO_IBGE_CODE.get(uf.upper())
    if codigo_uf is None:
        raise HTTPException(status_code=404, detail="Estado não encontrado")

    municipios = db.execute(
        select(Location).where(
            Location.type == LocationType.municipality,
            Location.code.like(f"{codigo_uf}%"),
        )
    ).scalars().all()

    result: list[MunicipioSummaryOut] = []
    for municipio in municipios:
        rows = db.execute(
            select(indicator_summary).where(indicator_summary.c.location_id == municipio.id)
        ).mappings().all()
        if not rows:
            continue

        last_dates = [row["last_date"] for row in rows if row["last_date"] is not None]
        result.append(
            MunicipioSummaryOut(
                code=municipio.code,
                name=municipio.name,
                uf=uf.upper(),
                indicators_available=len(rows),
                melhoraram=sum(1 for row in rows if row["classification"] == "MELHOROU"),
                pioraram=sum(1 for row in rows if row["classification"] == "PIOROU"),
                last_updated=max(last_dates) if last_dates else None,
            )
        )

    result.sort(key=lambda m: m.name)
    return result


@router.get("/{uf}/{codigo}", response_model=MunicipioDetailOut)
def get_municipio(uf: str, codigo: str, db: Session = Depends(get_db)) -> MunicipioDetailOut:
    municipio = db.execute(
        select(Location).where(Location.type == LocationType.municipality, Location.code == codigo)
    ).scalar_one_or_none()
    if municipio is None:
        raise HTTPException(status_code=404, detail="Município não encontrado")

    rows = db.execute(
        select(indicator_summary).where(indicator_summary.c.location_id == municipio.id)
    ).mappings().all()

    return MunicipioDetailOut(
        code=municipio.code,
        name=municipio.name,
        uf=uf.upper(),
        indicators=[IndicatorSummaryOut.model_validate(dict(row)) for row in rows],
    )
