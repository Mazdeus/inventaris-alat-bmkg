"""add_borrow_description_purpose

Revision ID: bb2c3d4e5f6a7
Revises: aa1b2c3d4e5f6
Create Date: 2026-08-23 00:10:00.000000

Menambahkan ke borrow_transactions:
- item_description (Deskripsi Barang, wajib untuk peminjaman baru)
- purpose          (Tujuan Barang, wajib untuk peminjaman baru)

Kolom nullable agar data lama aman; kewajiban isi di level aplikasi.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'bb2c3d4e5f6a7'
down_revision: Union[str, None] = 'aa1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("borrow_transactions")]

    if "item_description" not in cols:
        op.add_column(
            'borrow_transactions',
            sa.Column('item_description', sa.Text(), nullable=True,
                      comment='Deskripsi barang yang dipinjam'),
        )

    if "purpose" not in cols:
        op.add_column(
            'borrow_transactions',
            sa.Column('purpose', sa.Text(), nullable=True,
                      comment='Tujuan peminjaman'),
        )


def downgrade() -> None:
    op.drop_column('borrow_transactions', 'item_description')
    op.drop_column('borrow_transactions', 'purpose')
