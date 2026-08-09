from datetime import date
from uuid import UUID

from pydantic import BaseModel


class IndicatorSummaryOut(BaseModel):
    indicator_id: UUID
    slug: str
    name: str
    category: str
    unit: str
    polarity: str
    location_id: UUID
    first_date: date | None
    last_date: date | None
    first_value: float | None
    last_value: float | None
    change_absolute: float | None
    classification: str

    model_config = {"from_attributes": True}


class IndicatorValuePoint(BaseModel):
    reference_date: date
    value: float

    model_config = {"from_attributes": True}


class IndicatorDetailOut(BaseModel):
    slug: str
    name: str
    category: str
    unit: str
    polarity: str
    description_what: str | None
    description_how: str | None
    update_frequency: str | None
    source_name: str
    source_url: str
    methodology: str | None
    summary: IndicatorSummaryOut | None
    min_value: float | None
    max_value: float | None
    avg_value: float | None
    history: list[IndicatorValuePoint]


class GovernmentPeriodOut(BaseModel):
    level: str
    holder_name: str
    start_date: date
    end_date: date | None

    model_config = {"from_attributes": True}
