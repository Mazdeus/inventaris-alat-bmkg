"""update_transaction_numbers_and_fk_relation

Revision ID: zz2b3c4d5e6f
Revises: z2a3b4c5d6e7
Create Date: 2026-09-02 00:00:00.000000

1. Memperlebar kolom transaction_number pada borrow_transactions & returns menjadi VARCHAR(30).
2. Memastikan borrow_id BigInteger pada returns tetap menjadi Foreign Key ke borrow_transactions.id.
3. Menghapus foreign key string borrow_transaction_number jika sempat dibuat.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'zz2b3c4d5e6f'
down_revision: Union[str, None] = 'z2a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(conn, table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(conn)
    return column_name in [c["name"] for c in inspector.get_columns(table_name)]


def _has_fk(conn, table_name: str, fk_name: str) -> bool:
    inspector = sa.inspect(conn)
    return any(fk.get("name") == fk_name for fk in inspector.get_foreign_keys(table_name))


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Perlebar borrow_transactions.transaction_number ke VARCHAR(30)
    if _has_column(conn, "borrow_transactions", "transaction_number"):
        op.alter_column(
            'borrow_transactions',
            'transaction_number',
            existing_type=sa.String(11),
            type_=sa.String(30),
            existing_nullable=True,
            existing_comment="Nomor transaksi unik format PJ-YYYYMMDDNNN",
        )

    # 2. Perlebar returns.transaction_number ke VARCHAR(30)
    if _has_column(conn, "returns", "transaction_number"):
        op.alter_column(
            'returns',
            'transaction_number',
            existing_type=sa.String(11),
            type_=sa.String(30),
            existing_nullable=True,
            existing_comment="Nomor transaksi unik format KB-YYYYMMDDNNN",
        )

    # 3. Drop string foreign key constraint jika ada
    if _has_fk(conn, "returns", "fk_returns_borrow_tx_num"):
        op.drop_constraint('fk_returns_borrow_tx_num', 'returns', type_='foreignkey')

    if _has_column(conn, "returns", "borrow_transaction_number"):
        try:
            op.drop_constraint('uq_return_borrow_tx_num', 'returns', type_='unique')
        except Exception:
            pass
        op.drop_column('returns', 'borrow_transaction_number')

    # 4. Pastikan borrow_id NOT NULL di returns
    if _has_column(conn, "returns", "borrow_id"):
        op.alter_column(
            'returns',
            'borrow_id',
            existing_type=sa.BigInteger(),
            nullable=False,
        )


def downgrade() -> None:
    conn = op.get_bind()

    if _has_column(conn, "returns", "transaction_number"):
        op.alter_column(
            'returns',
            'transaction_number',
            existing_type=sa.String(30),
            type_=sa.String(11),
            existing_nullable=True,
        )

    if _has_column(conn, "borrow_transactions", "transaction_number"):
        op.alter_column(
            'borrow_transactions',
            'transaction_number',
            existing_type=sa.String(30),
            type_=sa.String(11),
            existing_nullable=True,
        )
