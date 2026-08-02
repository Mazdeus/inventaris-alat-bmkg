"""Make inventory_components.specifications nullable.

Revision ID: j1k2l3m4n5o6
Revises: i0j1k2l3m4n5
Create Date: 2026-07-28 01:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'j1k2l3m4n5o6'
down_revision: Union[str, None] = 'i0j1k2l3m4n5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('inventory_components', 'specifications',
                    existing_type=sa.Text(),
                    nullable=True)


def downgrade() -> None:
    op.alter_column('inventory_components', 'specifications',
                    existing_type=sa.Text(),
                    nullable=False)
