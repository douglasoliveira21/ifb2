import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.common import uuid_pk


class ScannedArticle(Base):
    """Registro de cada matéria de RSS já processada pela varredura de
    Frases Verificadas (app/sync/claim_scan.py) — evita reprocessar o
    mesmo link a cada execução (o job roda de 3 em 3 horas e os feeds
    mantêm os mesmos itens por várias horas/dias)."""

    __tablename__ = "scanned_articles"

    id: Mapped[uuid.UUID] = uuid_pk()
    url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    source_feed: Mapped[str] = mapped_column(Text, nullable=False)
    claim_extracted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
