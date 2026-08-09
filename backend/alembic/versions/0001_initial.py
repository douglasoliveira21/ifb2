"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "type",
            sa.Enum("country", "state", name="location_type"),
            nullable=False,
        ),
        sa.Column("code", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=False),
    )

    op.create_table(
        "indicator_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "ECONOMIA",
                "EMPREGO_RENDA",
                "SAUDE",
                "EDUCACAO",
                "SEGURANCA",
                "MEIO_AMBIENTE",
                "INFRAESTRUTURA",
                "CONTAS_PUBLICAS",
                name="indicator_category",
            ),
            nullable=False,
        ),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column(
            "polarity",
            sa.Enum("higher_is_better", "lower_is_better", "neutral", name="indicator_polarity"),
            nullable=False,
        ),
        sa.Column("description_what", sa.Text()),
        sa.Column("description_how", sa.Text()),
        sa.Column("update_frequency", sa.Text()),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "indicator_methodologies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "indicator_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("indicator_definitions.id"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "indicator_values",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "indicator_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("indicator_definitions.id"),
            nullable=False,
        ),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("locations.id"), nullable=False),
        sa.Column("reference_date", sa.Date(), nullable=False),
        sa.Column("value", sa.Numeric(), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("dataset_version", sa.Text()),
        sa.Column("is_revised", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "indicator_id", "location_id", "reference_date", "is_revised", name="uq_indicator_value_current"
        ),
    )
    op.create_index(
        "ix_indicator_values_lookup", "indicator_values", ["indicator_id", "location_id", "reference_date"]
    )

    op.create_table(
        "government_periods",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("locations.id"), nullable=False),
        sa.Column("level", sa.Enum("federal", "state", name="government_level"), nullable=False),
        sa.Column("holder_name", sa.Text(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date()),
    )

    op.create_table(
        "sync_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.Enum("success", "partial", "error", name="sync_status"), nullable=False),
        sa.Column("records_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text()),
    )

    op.create_table(
        "data_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "indicator_value_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("indicator_values.id"),
            nullable=False,
        ),
        sa.Column("previous_value", sa.Numeric(), nullable=False),
        sa.Column("new_value", sa.Numeric(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("changed_by", sa.Text(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Materialized view: pré-calcula valor inicial/atual/variação/classificação
    # por indicador x localização, usando o menor e o maior reference_date
    # disponíveis (versão vigente, is_revised = false) por par indicator/location.
    op.execute(
        """
        CREATE MATERIALIZED VIEW indicators AS
        WITH bounds AS (
            SELECT
                indicator_id,
                location_id,
                MIN(reference_date) AS first_date,
                MAX(reference_date) AS last_date
            FROM indicator_values
            WHERE is_revised = false
            GROUP BY indicator_id, location_id
        ),
        first_values AS (
            SELECT b.indicator_id, b.location_id, iv.value AS first_value
            FROM bounds b
            JOIN indicator_values iv
              ON iv.indicator_id = b.indicator_id
             AND iv.location_id = b.location_id
             AND iv.reference_date = b.first_date
             AND iv.is_revised = false
        ),
        last_values AS (
            SELECT b.indicator_id, b.location_id, iv.value AS last_value
            FROM bounds b
            JOIN indicator_values iv
              ON iv.indicator_id = b.indicator_id
             AND iv.location_id = b.location_id
             AND iv.reference_date = b.last_date
             AND iv.is_revised = false
        )
        SELECT
            d.id AS indicator_id,
            d.slug,
            d.name,
            d.category,
            d.unit,
            d.polarity,
            b.location_id,
            b.first_date,
            b.last_date,
            fv.first_value,
            lv.last_value,
            (lv.last_value - fv.first_value) AS change_absolute,
            CASE
                WHEN fv.first_value IS NULL OR lv.last_value IS NULL THEN 'SEM_DADOS'
                WHEN lv.last_value = fv.first_value THEN 'ESTAVEL'
                WHEN d.polarity = 'higher_is_better' AND lv.last_value > fv.first_value THEN 'MELHOROU'
                WHEN d.polarity = 'higher_is_better' AND lv.last_value < fv.first_value THEN 'PIOROU'
                WHEN d.polarity = 'lower_is_better' AND lv.last_value < fv.first_value THEN 'MELHOROU'
                WHEN d.polarity = 'lower_is_better' AND lv.last_value > fv.first_value THEN 'PIOROU'
                ELSE 'INCONCLUSIVO'
            END AS classification
        FROM indicator_definitions d
        JOIN bounds b ON b.indicator_id = d.id
        LEFT JOIN first_values fv ON fv.indicator_id = b.indicator_id AND fv.location_id = b.location_id
        LEFT JOIN last_values lv ON lv.indicator_id = b.indicator_id AND lv.location_id = b.location_id
        WHERE d.enabled = true
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX ix_indicators_pk ON indicators (indicator_id, location_id)"
    )


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS indicators")
    op.drop_table("data_revisions")
    op.drop_table("sync_runs")
    op.drop_table("government_periods")
    op.drop_index("ix_indicator_values_lookup", table_name="indicator_values")
    op.drop_table("indicator_values")
    op.drop_table("indicator_methodologies")
    op.drop_table("indicator_definitions")
    op.drop_table("locations")
    op.drop_table("sources")
    op.execute("DROP TYPE IF EXISTS sync_status")
    op.execute("DROP TYPE IF EXISTS government_level")
    op.execute("DROP TYPE IF EXISTS indicator_polarity")
    op.execute("DROP TYPE IF EXISTS indicator_category")
    op.execute("DROP TYPE IF EXISTS location_type")
