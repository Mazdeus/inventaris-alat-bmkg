"""add bmn_status and tx numbers to maintenance handover

Revision ID: zz5e6f7a8b9c
Revises: zz4d5e6f7a8b
Create Date: 2026-09-06 15:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'zz5e6f7a8b9c'
down_revision = 'zz4d5e6f7a8b'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Tambah bmn_status ke inventory_components
    op.add_column(
        'inventory_components',
        sa.Column('bmn_status', sa.String(length=50), server_default='BMN Pusat', nullable=False, comment='Status BMN unit (default: BMN Pusat)')
    )

    # 2. Tambah transaction_number & daily_sequence ke handovers
    op.add_column(
        'handovers',
        sa.Column('transaction_number', sa.String(length=20), nullable=True, comment='Nomor transaksi pelimpahan unik PL-YYYYMMDDNNN')
    )
    op.create_unique_constraint('uq_handovers_transaction_number', 'handovers', ['transaction_number'])
    op.add_column(
        'handovers',
        sa.Column('daily_sequence', sa.Integer(), nullable=True, comment='Nomor urut harian')
    )

    # 3. Tambah transaction_number & daily_sequence ke maintenance
    op.add_column(
        'maintenance',
        sa.Column('transaction_number', sa.String(length=20), nullable=True, comment='Nomor transaksi pemeliharaan unik PM-YYYYMMDDNNN')
    )
    op.create_unique_constraint('uq_maintenance_transaction_number', 'maintenance', ['transaction_number'])
    op.add_column(
        'maintenance',
        sa.Column('daily_sequence', sa.Integer(), nullable=True, comment='Nomor urut harian')
    )


def downgrade():
    # maintenance
    op.drop_constraint('uq_maintenance_transaction_number', 'maintenance', type_='unique')
    op.drop_column('maintenance', 'daily_sequence')
    op.drop_column('maintenance', 'transaction_number')

    # handovers
    op.drop_constraint('uq_handovers_transaction_number', 'handovers', type_='unique')
    op.drop_column('handovers', 'daily_sequence')
    op.drop_column('handovers', 'transaction_number')

    # inventory_components
    op.drop_column('inventory_components', 'bmn_status')
