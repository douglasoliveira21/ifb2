"""municipality location type

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-10

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Postgres permite ALTER TYPE ... ADD VALUE dentro de uma transação
    # (desde o PG12) contanto que o valor novo não seja usado na mesma
    # transação — só estamos declarando o valor aqui, não inserindo linhas.
    op.execute("ALTER TYPE location_type ADD VALUE IF NOT EXISTS 'municipality'")


def downgrade() -> None:
    # Postgres não suporta remover um valor de enum diretamente. Só é seguro
    # recriar o tipo se nenhuma linha estiver usando 'municipality' — aborta
    # em vez de apagar dado silenciosamente.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM locations WHERE type = 'municipality') THEN
                RAISE EXCEPTION 'Não é possível reverter: existem locations com type=municipality. Apague-as antes do downgrade.';
            END IF;
        END $$;
        """
    )
    op.execute("ALTER TYPE location_type RENAME TO location_type_old")
    op.execute("CREATE TYPE location_type AS ENUM ('country', 'state')")
    op.execute(
        "ALTER TABLE locations ALTER COLUMN type TYPE location_type USING type::text::location_type"
    )
    op.execute("DROP TYPE location_type_old")
