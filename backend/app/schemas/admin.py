from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.verified_claim import VerifiedClaimOut


class AdminIndicatorOut(BaseModel):
    slug: str
    name: str
    category: str
    unit: str
    source_name: str
    enabled: bool
    methodology: str | None
    methodology_version: int | None

    model_config = {"from_attributes": True}


class ToggleIndicatorIn(BaseModel):
    enabled: bool


class AdminSourceOut(BaseModel):
    name: str
    url: str
    description: str | None
    indicators_count: int


class AdminSyncRunOut(BaseModel):
    id: UUID
    source_name: str
    started_at: datetime
    finished_at: datetime | None
    status: str
    records_processed: int
    error_message: str | None


class AdminIndicatorValueOut(BaseModel):
    id: UUID
    location_code: str
    reference_date: date
    value: float
    is_revised: bool


class CorrectionIn(BaseModel):
    indicator_value_id: UUID
    new_value: float
    reason: str


class CorrectionOut(BaseModel):
    id: UUID
    indicator_slug: str
    location_code: str
    reference_date: date
    previous_value: float
    new_value: float
    reason: str
    changed_by: str
    changed_at: datetime


class VerifiedClaimIn(BaseModel):
    quote: str
    speaker_name: str
    speaker_role: str | None = None
    claim_date: date | None = None
    source_url: str | None = None
    indicator_slug: str | None = None
    verdict: str
    explanation: str


__all__ = [
    "AdminIndicatorOut",
    "AdminIndicatorValueOut",
    "AdminSourceOut",
    "AdminSyncRunOut",
    "CorrectionIn",
    "CorrectionOut",
    "ToggleIndicatorIn",
    "VerifiedClaimIn",
    "VerifiedClaimOut",
]
