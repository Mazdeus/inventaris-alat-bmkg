"""return_per_sn_status_document

Revision ID: q3r4s5t6u7v8
Revises: p2q3r4s5t6u7
Create Date: 2026-08-02 00:00:00.000000

Menambahkan:
- status, signed_document, late_reason, verified_at ke tabel returns
- tabel baru return_detail_items (tracking per SN)
- mengubah return_details.condition menjadi nullable
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = 'q3r4s5t6u7v8'
down_revision: Union[str, None] = 'p2q3r4s5t6u7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tambah kolom ke tabel returns
    op.add_column('returns',
                  sa.Column('status', sa.String(50), nullable=False,
                            server_default='Menunggu Verifikasi',
                            comment='Status pengembalian: Menunggu Verifikasi / Selesai'))
    op.add_column('returns',
                  sa.Column('signed_document', sa.String(255), nullable=True,
                            comment='Path dokumen pengembalian tertandatangan'))
    op.add_column('returns',
                  sa.Column('late_reason', sa.Text, nullable=True,
                            comment='Alasan keterlambatan pengembalian'))
    op.add_column('returns',
                  sa.Column('verified_at', sa.DateTime, nullable=True,
                            comment='Waktu verifikasi oleh admin'))

    # 2. Buat tabel return_detail_items (tracking per SN)
    op.create_table(
        'return_detail_items',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('return_detail_id', sa.BigInteger,
                  sa.ForeignKey('return_details.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('inventory_item_id', sa.BigInteger,
                  sa.ForeignKey('inventory_items.id', ondelete='RESTRICT'),
                  nullable=False),
        sa.Column('condition', sa.String(50), nullable=False,
                  comment='Kondisi: Baik / Rusak'),
        sa.Column('notes', sa.Text, nullable=True,
                  comment='Catatan per barang'),
        sa.UniqueConstraint('return_detail_id', 'inventory_item_id',
                            name='uq_return_detail_item'),
    )

    # 3. Ubah return_details.condition menjadi nullable
    op.alter_column('return_details', 'condition',
                    existing_type=sa.String(50),
                    nullable=True)


def downgrade() -> None:
    # 3. Kembalikan return_details.condition ke NOT NULL
    op.alter_column('return_details', 'condition',
                    existing_type=sa.String(50),
                    nullable=False)

    # 2. Hapus tabel return_detail_items
    op.drop_table('return_detail_items')

    # 1. Hapus kolom dari returns
    op.drop_column('returns', 'verified_at')
    op.drop_column('returns', 'late_reason')
    op.drop_column('returns', 'signed_document')
    op.drop_column('returns', 'status')
