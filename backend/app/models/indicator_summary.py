from sqlalchemy import Column, Date, Numeric, Table, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base

# Não gerenciada pelo Alembic como tabela — mapeia a materialized view
# `indicators`, criada na migration 0001, e recalculada por REFRESH
# MATERIALIZED VIEW ao final de cada sincronização.
indicator_summary = Table(
    "indicators",
    Base.metadata,
    Column("indicator_id", UUID(as_uuid=True), primary_key=True),
    Column("slug", Text),
    Column("name", Text),
    Column("category", Text),
    Column("unit", Text),
    Column("polarity", Text),
    Column("location_id", UUID(as_uuid=True), primary_key=True),
    Column("first_date", Date),
    Column("last_date", Date),
    Column("first_value", Numeric),
    Column("last_value", Numeric),
    Column("change_absolute", Numeric),
    Column("classification", Text),
    extend_existing=True,
)
