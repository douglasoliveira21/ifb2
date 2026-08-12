import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.common import uuid_pk


class ClaimVerdict(str, enum.Enum):
    CONFIRMADO = "CONFIRMADO"
    PARCIALMENTE_CONFIRMADO = "PARCIALMENTE_CONFIRMADO"
    DISTORCIDO = "DISTORCIDO"
    FALSO = "FALSO"
    INCONCLUSIVO = "INCONCLUSIVO"


class ClaimStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class ClaimOrigin(str, enum.Enum):
    MANUAL = "MANUAL"
    AI_SCAN = "AI_SCAN"


class VerifiedClaim(Base):
    """Uma citação de campanha/discurso checada contra um indicador real do
    IFB. Curadoria manual via /admin/frases-verificadas entra já como
    PUBLISHED; a varredura automática (app/sync/claim_scan.py) só grava
    como DRAFT — nunca publica sozinha, precisa de aprovação humana em
    /admin/frases-verificadas antes de aparecer em /frases-verificadas.
    Ver app/api/verified_claims.py."""

    __tablename__ = "verified_claims"

    id: Mapped[uuid.UUID] = uuid_pk()
    quote: Mapped[str] = mapped_column(Text, nullable=False)
    speaker_name: Mapped[str] = mapped_column(Text, nullable=False)
    speaker_role: Mapped[str | None] = mapped_column(Text)
    claim_date: Mapped[date | None] = mapped_column(Date)
    source_url: Mapped[str | None] = mapped_column(Text)
    indicator_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("indicator_definitions.id"))
    verdict: Mapped[ClaimVerdict] = mapped_column(Enum(ClaimVerdict, name="claim_verdict"), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ClaimStatus] = mapped_column(
        Enum(ClaimStatus, name="claim_status"), nullable=False, server_default=ClaimStatus.PUBLISHED.value
    )
    origin: Mapped[ClaimOrigin] = mapped_column(
        Enum(ClaimOrigin, name="claim_origin"), nullable=False, server_default=ClaimOrigin.MANUAL.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
