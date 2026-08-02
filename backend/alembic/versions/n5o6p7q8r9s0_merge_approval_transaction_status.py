"""Gabung approval_status + transaction_status menjadi kolom status tunggal.

Revision ID: n5o6p7q8r9s0
Revises: m4n5o6p7q8r9
Create Date: 2026-07-30 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'n5o6p7q8r9s0'
down_revision: Union[str, None] = 'm4n5o6p7q8r9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tambah kolom status baru
    op.add_column('borrow_transactions',
                  sa.Column('status', sa.String(50), nullable=False, server_default='Menunggu',
                            comment='Menunggu / Dipinjam / Dikembalikan / Dibatalkan'))

    # 2. Mapping data existing ke kolom status baru
    # Mapping logic:
    #   approval_status='Pending'                                                          → Menunggu
    #   approval_status='Approved' AND transaction_status='Borrowed'                       → Dipinjam
    #   transaction_status='Returned'                                                      → Dikembalikan
    #   approval_status='Rejected' OR transaction_status='Cancelled'                       → Dibatalkan
    op.execute("""
        UPDATE borrow_transactions SET status = CASE
            WHEN approval_status = 'Pending' THEN 'Menunggu'
            WHEN approval_status = 'Approved' AND transaction_status = 'Borrowed' THEN 'Dipinjam'
            WHEN transaction_status = 'Returned' THEN 'Dikembalikan'
            WHEN approval_status = 'Rejected' OR transaction_status = 'Cancelled' THEN 'Dibatalkan'
            ELSE 'Menunggu'
        END
    """)

    # 3. Hapus kolom lama
    op.drop_column('borrow_transactions', 'approval_status')
    op.drop_column('borrow_transactions', 'transaction_status')


def downgrade() -> None:
    # 1. Tambah kembali kolom approval_status dan transaction_status sebagai VARCHAR
    op.add_column('borrow_transactions',
                  sa.Column('approval_status', sa.String(50), nullable=False, server_default='Pending'))
    op.add_column('borrow_transactions',
                  sa.Column('transaction_status', sa.String(50), nullable=False, server_default='Borrowed'))

    # 2. Mapping balik dari status ke approval_status + transaction_status
    op.execute("""
        UPDATE borrow_transactions SET
            approval_status = CASE
                WHEN status = 'Menunggu' THEN 'Pending'
                WHEN status = 'Dipinjam' THEN 'Approved'
                WHEN status = 'Dikembalikan' THEN 'Approved'
                WHEN status = 'Dibatalkan' THEN 'Rejected'
                ELSE 'Pending'
            END,
            transaction_status = CASE
                WHEN status = 'Menunggu' THEN 'Borrowed'
                WHEN status = 'Dipinjam' THEN 'Borrowed'
                WHEN status = 'Dikembalikan' THEN 'Returned'
                WHEN status = 'Dibatalkan' THEN 'Cancelled'
                ELSE 'Borrowed'
            END
    """)

    # 3. Hapus kolom status
    op.drop_column('borrow_transactions', 'status')
