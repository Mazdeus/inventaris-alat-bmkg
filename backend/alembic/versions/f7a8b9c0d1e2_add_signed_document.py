"""Add signed_document column to borrow_transactions.

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-07-22 11:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'f7a8b9c0d1e2'
down_revision: Union[str, None] = 'e6f7a8b9c0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('borrow_transactions',
        sa.Column('signed_document', sa.String(255), nullable=True, comment='Path dokumen yang sudah ditandatangani'))


def downgrade() -> None:
    op.drop_column('borrow_transactions', 'signed_document')
