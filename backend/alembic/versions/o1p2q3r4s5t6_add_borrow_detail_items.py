"""Tambah tabel borrow_detail_items untuk tracking SN yang dipilih per transaksi.

Revision ID: o1p2q3r4s5t6
Revises: n5o6p7q8r9s0
Create Date: 2026-08-02 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'o1p2q3r4s5t6'
down_revision: Union[str, None] = 'n5o6p7q8r9s0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'borrow_detail_items',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('borrow_detail_id', sa.BigInteger(),
                  sa.ForeignKey('borrow_details.id', ondelete='CASCADE'), nullable=False),
        sa.Column('inventory_item_id', sa.BigInteger(),
                  sa.ForeignKey('inventory_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('borrow_detail_id', 'inventory_item_id',
                            name='uq_borrow_detail_item'),
    )


def downgrade() -> None:
    op.drop_table('borrow_detail_items')
