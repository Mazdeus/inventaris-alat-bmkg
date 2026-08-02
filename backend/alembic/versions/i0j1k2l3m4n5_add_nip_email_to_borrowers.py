"""Add nip and email to borrowers table.

Revision ID: i0j1k2l3m4n5
Revises: h9i0j1k2l3m4
Create Date: 2026-07-28 00:01:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'i0j1k2l3m4n5'
down_revision: Union[str, None] = 'h9i0j1k2l3m4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('borrowers', sa.Column('nip', sa.String(30), nullable=True))
    op.add_column('borrowers', sa.Column('email', sa.String(100), nullable=True))
    op.create_unique_constraint('uq_borrowers_nip', 'borrowers', ['nip'])
    op.create_unique_constraint('uq_borrowers_email', 'borrowers', ['email'])


def downgrade() -> None:
    op.drop_constraint('uq_borrowers_email', 'borrowers', type_='unique')
    op.drop_constraint('uq_borrowers_nip', 'borrowers', type_='unique')
    op.drop_column('borrowers', 'email')
    op.drop_column('borrowers', 'nip')
