"""enhance_activity_logs

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('activity_logs',
                  sa.Column('ip_address', sa.String(45), nullable=True,
                            comment='IP address pengguna saat aksi'))
    op.add_column('activity_logs',
                  sa.Column('user_agent', sa.String(255), nullable=True,
                            comment='User agent browser/aplikasi'))
    op.add_column('activity_logs',
                  sa.Column('extra_data', sa.Text(), nullable=True,
                            comment='Detail tambahan dalam format JSON'))


def downgrade() -> None:
    op.drop_column('activity_logs', 'extra_data')
    op.drop_column('activity_logs', 'user_agent')
    op.drop_column('activity_logs', 'ip_address')
