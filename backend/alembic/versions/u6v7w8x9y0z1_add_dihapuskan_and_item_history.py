"""add_dihapuskan_and_item_history

Revision ID: u6v7w8x9y0z1
Revises: t5u6v7w8x9y0
Create Date: 2026-08-03 00:00:00.000000

Menambahkan:
1. Status "Dihapuskan" ke inventory_status (soft delete)
2. Kolom deleted_at ke inventory_items
3. Tabel item_status_history untuk riwayat perubahan status barang
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


revision: str = 'u6v7w8x9y0z1'
down_revision: Union[str, None] = 't5u6v7w8x9y0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tambah status "Dihapuskan"
    op.execute(
        "INSERT INTO inventory_status (id, status_name) VALUES (5, 'Dihapuskan') "
        "ON DUPLICATE KEY UPDATE status_name = 'Dihapuskan'"
    )

    # 3. Buat tabel item_status_history
    op.create_table(
        'item_status_history',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('inventory_item_id', sa.BigInteger,
                  sa.ForeignKey('inventory_items.id', ondelete='CASCADE'),
                  nullable=False, comment='FK ke barang fisik'),
        sa.Column('inventory_component_id', sa.BigInteger,
                  sa.ForeignKey('inventory_components.id', ondelete='CASCADE'),
                  nullable=False, comment='FK ke komponen (denormalized untuk query)'),
        sa.Column('from_status_id', sa.BigInteger,
                  sa.ForeignKey('inventory_status.id', ondelete='SET NULL'),
                  nullable=True, comment='Status sebelum perubahan'),
        sa.Column('to_status_id', sa.BigInteger,
                  sa.ForeignKey('inventory_status.id', ondelete='RESTRICT'),
                  nullable=False, comment='Status setelah perubahan'),
        sa.Column('source', sa.String(50), nullable=False,
                  comment='Sumber perubahan: RETURN, ADMIN_TOGGLE, MAINTENANCE, DELETE'),
        sa.Column('return_id', sa.BigInteger,
                  sa.ForeignKey('returns.id', ondelete='SET NULL'),
                  nullable=True, comment='FK ke pengembalian (jika sumber RETURN)'),
        sa.Column('borrow_transaction_id', sa.BigInteger,
                  sa.ForeignKey('borrow_transactions.id', ondelete='SET NULL'),
                  nullable=True, comment='FK ke peminjaman (jika sumber RETURN)'),
        sa.Column('user_id', sa.BigInteger,
                  sa.ForeignKey('users.id', ondelete='SET NULL'),
                  nullable=True, comment='User yang melakukan perubahan'),
        sa.Column('notes', sa.Text, nullable=True,
                  comment='Catatan tambahan'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(),
                  comment='Waktu perubahan'),
    )


def downgrade() -> None:
    op.drop_table('item_status_history')
    op.execute("DELETE FROM inventory_status WHERE id = 5")
