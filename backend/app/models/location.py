import enum
import uuid

from sqlalchemy import Enum, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.common import uuid_pk


class LocationType(str, enum.Enum):
    country = "country"
    state = "state"


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = uuid_pk()
    type: Mapped[LocationType] = mapped_column(Enum(LocationType, name="location_type"), nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
