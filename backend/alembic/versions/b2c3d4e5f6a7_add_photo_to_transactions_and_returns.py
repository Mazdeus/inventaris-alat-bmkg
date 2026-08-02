"""add_photo_to_borrow_transactions_and_returns

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('borrow_transactions',
                  sa.Column('photo', sa.String(255), nullable=True,
                            comment='Path foto dokumentasi peminjaman'))
    op.add_column('returns',
                  sa.Column('photo', sa.String(255), nullable=True,
                            comment='Path foto dokumentasi pengembalian'))


def downgrade() -> None:
    op.drop_column('returns', 'photo')
    op.drop_column('borrow_transactions', 'photo')
