"""add_maintenance_officer

Revision ID: cc3d4e5f6a7b8
Revises: bb2c3d4e5f6a7
Create Date: 2026-08-23 00:20:00.000000

Menambahkan kolom officer_id (FK ke officers.id) pada tabel maintenance,
untuk mencatat petugas yang melakukan pemeliharaan. Wajib untuk data baru.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'cc3d4e5f6a7b8'
down_revision: Union[str, None] = 'bb2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("maintenance")]

    if "officer_id" not in cols:
        op.add_column(
            'maintenance',
            sa.Column('officer_id', sa.BigInteger(), nullable=True,
                      comment='ID petugas yang melakukan pemeliharaan'),
        )
        op.create_foreign_key(
            'fk_maintenance_officer_id',
            'maintenance', 'officers',
            ['officer_id'], ['id'],
            ondelete='SET NULL',
        )


def downgrade() -> None:
    op.drop_constraint('fk_maintenance_officer_id', 'maintenance', type_='foreignkey')
    op.drop_column('maintenance', 'officer_id')
