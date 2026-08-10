"""verified claims

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "verified_claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("quote", sa.Text(), nullable=False),
        sa.Column("speaker_name", sa.Text(), nullable=False),
        sa.Column("speaker_role", sa.Text()),
        sa.Column("claim_date", sa.Date()),
        sa.Column("source_url", sa.Text()),
        sa.Column(
            "indicator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("indicator_definitions.id")
        ),
        sa.Column(
            "verdict",
            sa.Enum(
                "CONFIRMADO",
                "PARCIALMENTE_CONFIRMADO",
                "DISTORCIDO",
                "FALSO",
                "INCONCLUSIVO",
                name="claim_verdict",
            ),
            nullable=False,
        ),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_verified_claims_created_at", "verified_claims", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_verified_claims_created_at", table_name="verified_claims")
    op.drop_table("verified_claims")
    op.execute("DROP TYPE IF EXISTS claim_verdict")
