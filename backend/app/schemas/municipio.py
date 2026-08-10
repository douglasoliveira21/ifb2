from datetime import date

from pydantic import BaseModel

from app.schemas.indicator import IndicatorSummaryOut


class MunicipioSummaryOut(BaseModel):
    code: str
    name: str
    uf: str
    indicators_available: int
    melhoraram: int
    pioraram: int
    last_updated: date | None


class MunicipioDetailOut(BaseModel):
    code: str
    name: str
    uf: str
    indicators: list[IndicatorSummaryOut]
