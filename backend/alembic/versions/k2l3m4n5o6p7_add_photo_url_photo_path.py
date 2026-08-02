"""Replace photo column with photo_url + photo_path (2 columns).

Revision ID: k2l3m4n5o6p7
Revises: j1k2l3m4n5o6
Create Date: 2026-07-28 01:01:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'k2l3m4n5o6p7'
down_revision: Union[str, None] = 'j1k2l3m4n5o6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns
    op.add_column('inventory_components', sa.Column('photo_url', sa.String(500), nullable=True))
    op.add_column('inventory_components', sa.Column('photo_path', sa.String(500), nullable=True))

    # Drop old column
    op.drop_column('inventory_components', 'photo')


def downgrade() -> None:
    op.add_column('inventory_components', sa.Column('photo', sa.String(255), nullable=True))
    op.drop_column('inventory_components', 'photo_path')
    op.drop_column('inventory_components', 'photo_url')
