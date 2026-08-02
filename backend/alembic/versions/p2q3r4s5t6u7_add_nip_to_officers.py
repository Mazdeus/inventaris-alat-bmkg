"""Tambah kolom NIP pada tabel officers.

Revision ID: p2q3r4s5t6u7
Revises: o1p2q3r4s5t6
Create Date: 2026-08-02 10:30:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'p2q3r4s5t6u7'
down_revision: Union[str, None] = 'o1p2q3r4s5t6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tambah kolom nip — nullable dulu
    op.add_column('officers',
                  sa.Column('nip', sa.String(30), nullable=True, unique=False))

    # 2. Backfill data existing dengan nip placeholder unik
    op.execute("UPDATE officers SET nip = CONCAT('TEMP_', LPAD(id, 6, '0')) WHERE nip IS NULL")

    # 3. Set NOT NULL
    op.alter_column('officers', 'nip', existing_type=sa.String(30), nullable=False)

    # 4. Tambah unique constraint
    op.create_unique_constraint('uq_officers_nip', 'officers', ['nip'])


def downgrade() -> None:
    op.drop_constraint('uq_officers_nip', 'officers', type_='unique')
    op.drop_column('officers', 'nip')
