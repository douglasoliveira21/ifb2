import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.common import uuid_pk


class IndicatorMethodology(Base):
    __tablename__ = "indicator_methodologies"

    id: Mapped[uuid.UUID] = uuid_pk()
    indicator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("indicator_definitions.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    indicator: Mapped["IndicatorDefinition"] = relationship(back_populates="methodologies")
