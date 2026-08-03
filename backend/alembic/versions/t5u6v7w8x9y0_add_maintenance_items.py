"""add_maintenance_items

Revision ID: t5u6v7w8x9y0
Revises: s4t5u6v7w8x9
Create Date: 2026-08-03 00:00:00.000000

Menambahkan tabel maintenance_items untuk mencatat barang fisik yang terlibat
dalam setiap record perawatan. Sebelumnya item_ids tidak dipersistenkan,
sehingga tidak bisa membedakan item mana yang milik record perawatan tertentu.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 't5u6v7w8x9y0'
down_revision: Union[str, None] = 's4t5u6v7w8x9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'maintenance_items',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('maintenance_id', sa.BigInteger,
                  sa.ForeignKey('maintenance.id', ondelete='CASCADE'),
                  nullable=False, comment='FK ke record perawatan'),
        sa.Column('inventory_item_id', sa.BigInteger,
                  sa.ForeignKey('inventory_items.id', ondelete='CASCADE'),
                  nullable=False, comment='FK ke barang fisik'),
        sa.Column('previous_status_id', sa.BigInteger,
                  sa.ForeignKey('inventory_status.id', ondelete='SET NULL'),
                  nullable=True, comment='Status barang sebelum perawatan'),
    )


def downgrade() -> None:
    op.drop_table('maintenance_items')
