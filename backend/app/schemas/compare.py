from pydantic import BaseModel

from app.schemas.indicator import IndicatorValuePoint


class CompareIndicatorOut(BaseModel):
    slug: str
    name: str
    category: str
    unit: str
    polarity: str
    history: list[IndicatorValuePoint]
