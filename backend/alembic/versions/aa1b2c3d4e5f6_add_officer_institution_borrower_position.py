"""add_officer_institution_borrower_position

Revision ID: aa1b2c3d4e5f6
Revises: z1a2b3c4d5e6
Create Date: 2026-08-23 00:00:00.000000

Menambahkan:
- officers.institution  (Instansi/unit kerja petugas, wajib untuk data baru)
- borrowers.position    (Jabatan peminjam, wajib untuk data baru)

Kolom dibuat nullable agar data lama tetap aman; kewajiban isi diberlakukan
di level aplikasi (Pydantic + validasi frontend).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'aa1b2c3d4e5f6'
down_revision: Union[str, None] = 'b3c4d5e6f7g8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # officers.institution
    off_cols = [c["name"] for c in inspector.get_columns("officers")]
    if "institution" not in off_cols:
        op.add_column(
            'officers',
            sa.Column('institution', sa.String(150), nullable=True,
                      comment='Instansi/unit kerja petugas'),
        )

    # borrowers.position
    bor_cols = [c["name"] for c in inspector.get_columns("borrowers")]
    if "position" not in bor_cols:
        op.add_column(
            'borrowers',
            sa.Column('position', sa.String(100), nullable=True,
                      comment='Jabatan peminjam'),
        )


def downgrade() -> None:
    op.drop_column('officers', 'institution')
    op.drop_column('borrowers', 'position')
