from datetime import date

from pydantic import BaseModel


class RankingListItemOut(BaseModel):
    slug: str
    indicator_name: str
    category: str
    unit: str
    polarity: str
    states_count: int
    last_updated: date | None


class RankingEntryOut(BaseModel):
    rank: int
    state_code: str
    state_name: str
    first_value: float
    last_value: float
    change_absolute: float
    classification: str
    first_date: date
    last_date: date


class RankingDetailOut(BaseModel):
    slug: str
    indicator_name: str
    category: str
    unit: str
    polarity: str
    entries: list[RankingEntryOut]
