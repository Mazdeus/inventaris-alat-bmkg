"""add_deleted_at_to_borrowers

Revision ID: x2y3z4a5b6c7
Revises: w1x2y3z4a5b6
Create Date: 2026-08-12 00:00:00.000000

Menambahkan kolom deleted_at untuk soft delete peminjam.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'x2y3z4a5b6c7'
down_revision: Union[str, None] = 'w1x2y3z4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('borrowers',
        sa.Column('deleted_at', sa.DateTime(), nullable=True,
                  comment='Timestamp saat peminjam dihapus (soft delete)')
    )


def downgrade() -> None:
    op.drop_column('borrowers', 'deleted_at')
