"""ai claim scan

Revision ID: 0021
Revises: 0020
Create Date: 2026-08-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0021"
down_revision: Union[str, None] = "0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    claim_status = sa.Enum("DRAFT", "PUBLISHED", name="claim_status")
    claim_origin = sa.Enum("MANUAL", "AI_SCAN", name="claim_origin")
    claim_status.create(op.get_bind())
    claim_origin.create(op.get_bind())

    op.add_column(
        "verified_claims",
        sa.Column("status", claim_status, nullable=False, server_default="PUBLISHED"),
    )
    op.add_column(
        "verified_claims",
        sa.Column("origin", claim_origin, nullable=False, server_default="MANUAL"),
    )
    op.create_index("ix_verified_claims_status", "verified_claims", ["status"])

    op.create_table(
        "scanned_articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("url", sa.Text(), nullable=False, unique=True),
        sa.Column("source_feed", sa.Text(), nullable=False),
        sa.Column("claim_extracted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("scanned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_scanned_articles_url", "scanned_articles", ["url"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_scanned_articles_url", table_name="scanned_articles")
    op.drop_table("scanned_articles")
    op.drop_index("ix_verified_claims_status", table_name="verified_claims")
    op.drop_column("verified_claims", "origin")
    op.drop_column("verified_claims", "status")
    op.execute("DROP TYPE IF EXISTS claim_origin")
    op.execute("DROP TYPE IF EXISTS claim_status")
