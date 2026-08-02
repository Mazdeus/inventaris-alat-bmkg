"""add_borrow_extensions

Revision ID: s4t5u6v7w8x9
Revises: q3r4s5t6u7v8
Create Date: 2026-08-03 00:00:00.000000

Menambahkan tabel borrow_extensions untuk perpanjangan peminjaman.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 's4t5u6v7w8x9'
down_revision: Union[str, None] = 'q3r4s5t6u7v8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'borrow_extensions',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('borrow_id', sa.BigInteger,
                  sa.ForeignKey('borrow_transactions.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('requested_by', sa.BigInteger,
                  sa.ForeignKey('users.id', ondelete='SET NULL'),
                  nullable=True, comment='User yang mengajukan perpanjangan'),
        sa.Column('requested_return_date', sa.Date, nullable=False,
                  comment='Tanggal kembali yang diajukan'),
        sa.Column('reason', sa.Text, nullable=True,
                  comment='Alasan perpanjangan'),
        sa.Column('status', sa.String(50), nullable=False,
                  server_default='Menunggu',
                  comment='Status: Menunggu / Disetujui / Ditolak'),
        sa.Column('approved_by', sa.BigInteger,
                  sa.ForeignKey('users.id', ondelete='SET NULL'),
                  nullable=True, comment='Admin yang memverifikasi'),
        sa.Column('approved_at', sa.DateTime, nullable=True,
                  comment='Waktu verifikasi'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('borrow_extensions')
