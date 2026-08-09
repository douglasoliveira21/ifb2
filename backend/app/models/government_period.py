import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.common import uuid_pk


class GovernmentLevel(str, enum.Enum):
    federal = "federal"
    state = "state"


class GovernmentPeriod(Base):
    __tablename__ = "government_periods"

    id: Mapped[uuid.UUID] = uuid_pk()
    location_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("locations.id"), nullable=False)
    level: Mapped[GovernmentLevel] = mapped_column(Enum(GovernmentLevel, name="government_level"), nullable=False)
    holder_name: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
