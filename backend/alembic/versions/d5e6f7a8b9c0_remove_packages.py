"""Remove inventory_packages table and FK from inventory_components.

Revision ID: d5e6f7a8b9c0
Revises: c3d4e5f6a7b8
Create Date: 2026-07-22 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop foreign key constraint on inventory_components
    op.drop_constraint('inventory_components_ibfk_1', 'inventory_components', type_='foreignkey')
    # Drop the column
    op.drop_column('inventory_components', 'inventory_package_id')
    # Drop inventory_packages table
    op.drop_table('inventory_packages')


def downgrade() -> None:
    # Recreate inventory_packages table
    op.create_table('inventory_packages',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('box_number', sa.String(length=50), nullable=False),
        sa.Column('photo', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('box_number'),
    )
    # Recreate FK column in inventory_components
    op.add_column('inventory_components',
        sa.Column('inventory_package_id', sa.BigInteger(), nullable=True))
    op.create_foreign_key('inventory_components_ibfk_1', 'inventory_components', 'inventory_packages',
                          ['inventory_package_id'], ['id'])
