from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class VerifiedClaimOut(BaseModel):
    id: UUID
    quote: str
    speaker_name: str
    speaker_role: str | None
    claim_date: date | None
    source_url: str | None
    indicator_slug: str | None
    verdict: str
    explanation: str
    created_at: datetime
