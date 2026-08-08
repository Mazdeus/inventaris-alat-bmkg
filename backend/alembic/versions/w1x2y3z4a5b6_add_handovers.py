"""add_handovers

Revision ID: w1x2y3z4a5b6
Revises: v5w6x7y8z9a0
Create Date: 2026-08-08 00:00:00.000000

Menambahkan:
1. Status "Dilimpahkan" ke inventory_status (id=6)
2. Tabel handovers — transaksi pelimpahan ke UPT
3. Tabel handover_items — barang yang dilimpahkan
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'w1x2y3z4a5b6'
down_revision: Union[str, None] = 'v5w6x7y8z9a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tambah status "Dilimpahkan"
    op.execute(
        "INSERT INTO inventory_status (id, status_name) VALUES (6, 'Dilimpahkan') "
        "ON DUPLICATE KEY UPDATE status_name = 'Dilimpahkan'"
    )

    # 2. Tabel handovers
    op.create_table(
        'handovers',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('upt_receiver', sa.String(100), nullable=False, comment='UPT penerima barang'),
        sa.Column('issued_by', sa.BigInteger, sa.ForeignKey('officers.id', ondelete='SET NULL'),
                  nullable=True, comment='ID petugas yang menyerahkan'),
        sa.Column('handover_date', sa.Date, nullable=False, comment='Tanggal pelimpahan'),
        sa.Column('status', sa.String(50), nullable=False, server_default='Draft',
                  comment='Status: Draft / Dilimpahkan / Dibatalkan'),
        sa.Column('photo', sa.String(255), nullable=True, comment='Path foto dokumentasi pelimpahan'),
        sa.Column('signed_document', sa.String(255), nullable=True, comment='Path dokumen tertandatangan'),
        sa.Column('notes', sa.Text, nullable=True, comment='Catatan pelimpahan'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True, comment='Waktu pelimpahan selesai'),
    )

    # 3. Tabel handover_items
    op.create_table(
        'handover_items',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('handover_id', sa.BigInteger, sa.ForeignKey('handovers.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('inventory_item_id', sa.BigInteger,
                  sa.ForeignKey('inventory_items.id', ondelete='RESTRICT'),
                  nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_unique_constraint('uq_handover_item', 'handover_items',
                                ['handover_id', 'inventory_item_id'])


def downgrade() -> None:
    op.drop_table('handover_items')
    op.drop_table('handovers')
    op.execute("DELETE FROM inventory_status WHERE id = 6")
