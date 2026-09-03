"""add maintenance_id and handover_id to item_status_history

Revision ID: zz3c4d5e6f7a
Revises: zz2b3c4d5e6f
Create Date: 2026-09-02 20:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'zz3c4d5e6f7a'
down_revision: Union[str, None] = 'zz2b3c4d5e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'item_status_history',
        sa.Column('maintenance_id', sa.BigInteger(),
                  sa.ForeignKey('maintenance.id', ondelete='SET NULL'),
                  nullable=True, comment='FK ke pemeliharaan')
    )
    op.add_column(
        'item_status_history',
        sa.Column('handover_id', sa.BigInteger(),
                  sa.ForeignKey('handovers.id', ondelete='SET NULL'),
                  nullable=True, comment='FK ke pelimpahan')
    )


def downgrade() -> None:
    op.drop_column('item_status_history', 'handover_id')
    op.drop_column('item_status_history', 'maintenance_id')
