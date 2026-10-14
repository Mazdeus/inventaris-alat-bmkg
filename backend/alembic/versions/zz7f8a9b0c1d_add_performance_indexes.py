"""add performance indexes

Adds secondary indexes on the most frequently filtered/joined columns to avoid
full table scans as data grows. This is part of the performance optimization
(documentation: perbaikan/perbaikan-53-optimasi-kinerja-loading-data.md).

Revision ID: zz7f8a9b0c1d
Revises: zz6f7a8b9c0d
Create Date: 2026-10-14 12:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'zz7f8a9b0c1d'
down_revision = 'zz6f7a8b9c0d'
branch_labels = None
depends_on = None


def upgrade():
    # inventory_items — filtered/joined by component and status everywhere
    op.create_index('ix_inventory_items_component_id', 'inventory_items', ['inventory_component_id'])
    op.create_index('ix_inventory_items_status_id', 'inventory_items', ['status_id'])
    op.create_index(
        'ix_inventory_items_component_status',
        'inventory_items',
        ['inventory_component_id', 'status_id'],
    )

    # inventory_components — soft-delete filter on list queries
    op.create_index('ix_inventory_components_deleted_at', 'inventory_components', ['deleted_at'])

    # borrow_transactions — status and date filters on list/dashboard queries
    op.create_index('ix_borrow_transactions_status', 'borrow_transactions', ['status'])
    op.create_index('ix_borrow_transactions_borrow_date', 'borrow_transactions', ['borrow_date'])
    op.create_index('ix_borrow_transactions_expected_return', 'borrow_transactions', ['expected_return_date'])

    # returns — date filter on list queries
    op.create_index('ix_returns_return_date', 'returns', ['return_date'])

    # item_status_history — history lookup per item ordered by created_at
    op.create_index(
        'ix_item_status_history_item_created',
        'item_status_history',
        ['inventory_item_id', 'created_at'],
    )

    # maintenance / handovers — date filters on list queries
    op.create_index('ix_maintenance_start_date', 'maintenance', ['start_date'])
    op.create_index('ix_handovers_handover_date', 'handovers', ['handover_date'])


def downgrade():
    op.drop_index('ix_handovers_handover_date', table_name='handovers')
    op.drop_index('ix_maintenance_start_date', table_name='maintenance')
    op.drop_index('ix_item_status_history_item_created', table_name='item_status_history')
    op.drop_index('ix_returns_return_date', table_name='returns')
    op.drop_index('ix_borrow_transactions_expected_return', table_name='borrow_transactions')
    op.drop_index('ix_borrow_transactions_borrow_date', table_name='borrow_transactions')
    op.drop_index('ix_borrow_transactions_status', table_name='borrow_transactions')
    op.drop_index('ix_inventory_components_deleted_at', table_name='inventory_components')
    op.drop_index('ix_inventory_items_component_status', table_name='inventory_items')
    op.drop_index('ix_inventory_items_status_id', table_name='inventory_items')
    op.drop_index('ix_inventory_items_component_id', table_name='inventory_items')
