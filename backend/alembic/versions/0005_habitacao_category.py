"""habitacao indicator category

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-11

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE indicator_category ADD VALUE IF NOT EXISTS 'HABITACAO'")


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM indicator_definitions WHERE category = 'HABITACAO') THEN
                RAISE EXCEPTION 'Não é possível reverter: existem indicator_definitions com category=HABITACAO. Apague-os antes do downgrade.';
            END IF;
        END $$;
        """
    )
    op.execute("ALTER TYPE indicator_category RENAME TO indicator_category_old")
    op.execute(
        """
        CREATE TYPE indicator_category AS ENUM (
            'ECONOMIA', 'EMPREGO_RENDA', 'SAUDE', 'EDUCACAO', 'SEGURANCA',
            'MEIO_AMBIENTE', 'INFRAESTRUTURA', 'CONTAS_PUBLICAS', 'DEMOGRAFIA'
        )
        """
    )
    op.execute(
        "ALTER TABLE indicator_definitions ALTER COLUMN category TYPE indicator_category USING category::text::indicator_category"
    )
    op.execute("DROP TYPE indicator_category_old")
