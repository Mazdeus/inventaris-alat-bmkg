"""Add officers table and alter issued_by/received_by to FK.

Revision ID: h9i0j1k2l3m4
Revises: g8h9i0j1k2l3
Create Date: 2026-07-28 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'h9i0j1k2l3m4'
down_revision: Union[str, None] = 'g8h9i0j1k2l3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Create officers table ──
    op.create_table(
        'officers',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('officer_name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(100), nullable=True),
        sa.Column('position', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── 2. Alter borrow_transactions.issued_by: VARCHAR(100) → BIGINT → FK officers.id ──
    op.alter_column('borrow_transactions', 'issued_by',
                    existing_type=sa.String(100),
                    type_=sa.BigInteger(),
                    existing_nullable=True,
                    postgresql_using='issued_by::bigint')
    op.create_foreign_key(
        'fk_borrow_transactions_issued_by',
        'borrow_transactions', 'officers',
        ['issued_by'], ['id'],
        ondelete='SET NULL',
    )

    # ── 3. Alter returns.received_by: VARCHAR(100) → BIGINT → FK officers.id ──
    op.alter_column('returns', 'received_by',
                    existing_type=sa.String(100),
                    type_=sa.BigInteger(),
                    existing_nullable=True,
                    postgresql_using='received_by::bigint')
    op.create_foreign_key(
        'fk_returns_received_by',
        'returns', 'officers',
        ['received_by'], ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    # ── 3. Reverse returns.received_by ──
    op.drop_constraint('fk_returns_received_by', 'returns', type_='foreignkey')
    op.alter_column('returns', 'received_by',
                    existing_type=sa.BigInteger(),
                    type_=sa.String(100),
                    existing_nullable=True)

    # ── 2. Reverse borrow_transactions.issued_by ──
    op.drop_constraint('fk_borrow_transactions_issued_by', 'borrow_transactions', type_='foreignkey')
    op.alter_column('borrow_transactions', 'issued_by',
                    existing_type=sa.BigInteger(),
                    type_=sa.String(100),
                    existing_nullable=True)

    # ── 1. Drop officers table ──
    op.drop_table('officers')
