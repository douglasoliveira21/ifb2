from datetime import date

from pydantic import BaseModel

from app.schemas.indicator import IndicatorSummaryOut


class StateSummaryOut(BaseModel):
    code: str
    name: str
    indicators_available: int
    melhoraram: int
    pioraram: int
    last_updated: date | None


class StateDetailOut(BaseModel):
    code: str
    name: str
    indicators: list[IndicatorSummaryOut]
