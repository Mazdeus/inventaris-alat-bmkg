"""add_phone_email_to_users

Revision ID: v5w6x7y8z9a0
Revises: u6v7w8x9y0z1
Create Date: 2026-08-08 00:00:00.000000

Menambahkan:
1. Kolom phone VARCHAR(20) ke users (wajib)
2. Kolom email VARCHAR(100) UNIQUE ke users (wajib)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'v5w6x7y8z9a0'
down_revision: Union[str, None] = 'u6v7w8x9y0z1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True, comment='Nomor telepon admin'))
    op.add_column('users', sa.Column('email', sa.String(100), nullable=True, comment='Email admin'))
    op.create_unique_constraint('uq_users_email', 'users', ['email'])


def downgrade() -> None:
    op.drop_constraint('uq_users_email', 'users', type_='unique')
    op.drop_column('users', 'email')
    op.drop_column('users', 'phone')
