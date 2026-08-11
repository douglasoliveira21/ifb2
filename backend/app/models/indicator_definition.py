import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.common import uuid_pk


class IndicatorCategory(str, enum.Enum):
    ECONOMIA = "ECONOMIA"
    EMPREGO_RENDA = "EMPREGO_RENDA"
    SAUDE = "SAUDE"
    EDUCACAO = "EDUCACAO"
    SEGURANCA = "SEGURANCA"
    MEIO_AMBIENTE = "MEIO_AMBIENTE"
    INFRAESTRUTURA = "INFRAESTRUTURA"
    CONTAS_PUBLICAS = "CONTAS_PUBLICAS"
    DEMOGRAFIA = "DEMOGRAFIA"
    HABITACAO = "HABITACAO"


class IndicatorPolarity(str, enum.Enum):
    higher_is_better = "higher_is_better"
    lower_is_better = "lower_is_better"
    neutral = "neutral"


class IndicatorDefinition(Base):
    __tablename__ = "indicator_definitions"

    id: Mapped[uuid.UUID] = uuid_pk()
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[IndicatorCategory] = mapped_column(
        Enum(IndicatorCategory, name="indicator_category"), nullable=False
    )
    unit: Mapped[str] = mapped_column(Text, nullable=False)
    polarity: Mapped[IndicatorPolarity] = mapped_column(
        Enum(IndicatorPolarity, name="indicator_polarity"), nullable=False
    )
    description_what: Mapped[str | None] = mapped_column(Text)
    description_how: Mapped[str | None] = mapped_column(Text)
    update_frequency: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    source: Mapped["Source"] = relationship(back_populates="indicator_definitions")
    values: Mapped[list["IndicatorValue"]] = relationship(back_populates="indicator")
    methodologies: Mapped[list["IndicatorMethodology"]] = relationship(back_populates="indicator")
