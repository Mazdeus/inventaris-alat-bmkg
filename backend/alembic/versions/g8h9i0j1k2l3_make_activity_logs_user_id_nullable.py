"""Make activity_logs.user_id nullable — untuk public uploads tanpa login.

Revision ID: g8h9i0j1k2l3
Revises: f7a8b9c0d1e2
Create Date: 2026-07-23 08:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'g8h9i0j1k2l3'
down_revision: Union[str, None] = 'f7a8b9c0d1e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('activity_logs', 'user_id',
                    existing_type=sa.BigInteger(),
                    nullable=True)


def downgrade() -> None:
    # Kembalikan ke NOT NULL — pastikan tidak ada row dengan user_id NULL
    op.execute("UPDATE activity_logs SET user_id = 1 WHERE user_id IS NULL")
    op.alter_column('activity_logs', 'user_id',
                    existing_type=sa.BigInteger(),
                    nullable=False)
