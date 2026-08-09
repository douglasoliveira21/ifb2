from datetime import date, datetime

from pydantic import BaseModel


class TransparencySourceOut(BaseModel):
    name: str
    url: str
    description: str | None


class TransparencySyncOut(BaseModel):
    source_name: str
    status: str
    finished_at: datetime | None
    records_processed: int


class TransparencyErrorOut(BaseModel):
    source_name: str
    started_at: datetime
    error_message: str | None


class TransparencyCorrectionOut(BaseModel):
    indicator_slug: str
    indicator_name: str
    location_code: str
    reference_date: date
    previous_value: float
    new_value: float
    reason: str
    changed_at: datetime


class TransparencyMethodologyOut(BaseModel):
    indicator_slug: str
    indicator_name: str
    version: int
    published_at: datetime


class TransparencyOut(BaseModel):
    sources: list[TransparencySourceOut]
    last_syncs: list[TransparencySyncOut]
    known_errors: list[TransparencyErrorOut]
    recent_corrections: list[TransparencyCorrectionOut]
    methodologies: list[TransparencyMethodologyOut]
