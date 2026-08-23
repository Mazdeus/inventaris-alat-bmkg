"""add_procurement_month

Revision ID: z1a2b3c4d5e6
Revises: y3z4a5b6c7d8
Create Date: 2026-08-19 00:00:00.000000

Menambahkan kolom procurement_month (1-12) ke inventory_components.
Bulan pengadaan menjadi wajib agar grafik pengadaan per bulan di dashboard akurat.

Catatan MySQL: DDL non-transaksional, jadi migration ini dibuat idempotent
(jika kolom sudah terlanjur dibuat oleh percobaan sebelumnya, add_column dilewati).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'z1a2b3c4d5e6'
down_revision: Union[str, None] = 'y3z4a5b6c7d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols = [c["name"] for c in inspector.get_columns("inventory_components")]

    if "procurement_month" not in existing_cols:
        op.add_column(
            'inventory_components',
            sa.Column('procurement_month', sa.Integer, nullable=True,
                      comment='Bulan pengadaan (1-12)'),
        )

    # Backfill data lama dengan 1 (Januari)
    op.execute(
        "UPDATE inventory_components SET procurement_month = 1 "
        "WHERE procurement_month IS NULL"
    )

    # MySQL mensyaratkan existing_type untuk operasi CHANGE/MODIFY COLUMN
    op.alter_column(
        'inventory_components', 'procurement_month',
        nullable=False, server_default='1',
        existing_type=sa.Integer(),
    )


def downgrade() -> None:
    op.drop_column('inventory_components', 'procurement_month')
