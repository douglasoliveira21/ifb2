import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.common import uuid_pk


class DataRevision(Base):
    __tablename__ = "data_revisions"

    id: Mapped[uuid.UUID] = uuid_pk()
    indicator_value_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("indicator_values.id"), nullable=False)
    previous_value: Mapped[float] = mapped_column(Numeric, nullable=False)
    new_value: Mapped[float] = mapped_column(Numeric, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    changed_by: Mapped[str] = mapped_column(Text, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
