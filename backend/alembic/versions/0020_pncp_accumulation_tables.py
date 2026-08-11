"""pncp accumulation tables

Revision ID: 0020
Revises: 0019
Create Date: 2026-08-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0020"
down_revision: Union[str, None] = "0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pncp_sync_checkpoints",
        sa.Column("modalidade_codigo", sa.Integer(), primary_key=True),
        sa.Column("ultima_data_final", sa.Date(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "pncp_contratacao_totals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("uf", sa.String(length=2), nullable=False),
        sa.Column("modalidade_codigo", sa.Integer(), nullable=False),
        sa.Column("valor_total", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("ano", "uf", "modalidade_codigo", name="uq_pncp_total_ano_uf_modalidade"),
    )


def downgrade() -> None:
    op.drop_table("pncp_contratacao_totals")
    op.drop_table("pncp_sync_checkpoints")
