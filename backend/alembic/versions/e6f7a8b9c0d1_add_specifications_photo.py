"""Add specifications and photo columns to inventory_components.

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-07-22 10:30:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'e6f7a8b9c0d1'
down_revision: Union[str, None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # MySQL doesn't allow DEFAULT for TEXT columns.
    # Add as nullable first, update existing rows, then alter to NOT NULL.
    op.add_column('inventory_components',
        sa.Column('specifications', sa.Text(), nullable=True, comment='Spesifikasi teknis komponen'))
    op.execute("UPDATE inventory_components SET specifications = '' WHERE specifications IS NULL")
    op.alter_column('inventory_components', 'specifications', nullable=False,
                    existing_type=sa.Text(), existing_comment='Spesifikasi teknis komponen')
    op.add_column('inventory_components',
        sa.Column('photo', sa.String(255), nullable=True, comment='Path/URL foto komponen'))


def downgrade() -> None:
    op.drop_column('inventory_components', 'photo')
    op.drop_column('inventory_components', 'specifications')
