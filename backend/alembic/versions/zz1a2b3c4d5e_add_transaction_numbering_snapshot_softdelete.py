"""add_transaction_numbering_snapshot_softdelete

Revision ID: zz1a2b3c4d5e
Revises: cc3d4e5f6a7b8
Create Date: 2026-08-26 00:00:00.000000

Menambahkan:
1. Tabel transaction_counters — counter nomor transaksi harian (atomic)
2. Kolom transaction_number & daily_sequence ke borrow_transactions & returns
3. Tabel transaction_snapshots — arsip transaksi selesai (JSON)
4. Kolom deleted_at ke officers & inventory_components (soft delete)
5. Kolom reference_path ke activity_logs (link ke transaksi terkait)

Catatan MySQL: DDL non-transaksional, migration dibuat idempotent
(kolom yang sudah ada dilewati).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'zz1a2b3c4d5e'
down_revision: Union[str, None] = 'cc3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(conn, table_name: str) -> bool:
    inspector = sa.inspect(conn)
    return table_name in inspector.get_table_names()


def _has_column(conn, table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(conn)
    return column_name in [c["name"] for c in inspector.get_columns(table_name)]


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Tabel transaction_counters
    if not _has_table(conn, "transaction_counters"):
        op.create_table(
            'transaction_counters',
            sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
            sa.Column('counter_type', sa.String(50), nullable=False,
                      comment="Jenis counter: 'borrow' / 'return'"),
            sa.Column('counter_date', sa.Date, nullable=False,
                      comment="Tanggal counter (reset harian)"),
            sa.Column('last_sequence', sa.Integer, nullable=False, server_default='0',
                      comment="Nomor urut terakhir pada tanggal tersebut"),
        )
        op.create_unique_constraint(
            'uq_transaction_counter', 'transaction_counters',
            ['counter_type', 'counter_date'],
        )

    # 2. Kolom nomor transaksi di borrow_transactions
    if not _has_column(conn, "borrow_transactions", "transaction_number"):
        op.add_column('borrow_transactions',
                      sa.Column('transaction_number', sa.String(11), nullable=True,
                                comment='Nomor transaksi unik format YYYYMMDDNNN'))
        op.create_unique_constraint(
            'uq_borrow_transaction_number', 'borrow_transactions',
            ['transaction_number'],
        )
    if not _has_column(conn, "borrow_transactions", "daily_sequence"):
        op.add_column('borrow_transactions',
                      sa.Column('daily_sequence', sa.Integer, nullable=True,
                                comment='Nomor urut harian (reset per hari)'))

    # 3. Kolom nomor transaksi di returns
    if not _has_column(conn, "returns", "transaction_number"):
        op.add_column('returns',
                      sa.Column('transaction_number', sa.String(11), nullable=True,
                                comment='Nomor transaksi unik format YYYYMMDDNNN'))
        op.create_unique_constraint(
            'uq_return_transaction_number', 'returns',
            ['transaction_number'],
        )
    if not _has_column(conn, "returns", "daily_sequence"):
        op.add_column('returns',
                      sa.Column('daily_sequence', sa.Integer, nullable=True,
                                comment='Nomor urut harian (reset per hari)'))

    # 4. Tabel transaction_snapshots
    if not _has_table(conn, "transaction_snapshots"):
        op.create_table(
            'transaction_snapshots',
            sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
            sa.Column('transaction_type', sa.String(50), nullable=False,
                      comment="Jenis: 'borrow' / 'return' / 'handover' / 'maintenance'"),
            sa.Column('transaction_id', sa.BigInteger, nullable=False,
                      comment="ID asli di tabel transaksi terkait"),
            sa.Column('snapshot_data', sa.JSON, nullable=False,
                      comment="Snapshot data transaksi saat selesai (JSON)"),
            sa.Column('completed_at', sa.DateTime, nullable=False,
                      comment="Waktu transaksi selesai/dibatalkan"),
            sa.Column('archived_by', sa.BigInteger, sa.ForeignKey('users.id', ondelete='SET NULL'),
                      nullable=True, comment="User yang menyelesaikan/mengarsipkan"),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        )
        op.create_index('idx_snapshot_type_id', 'transaction_snapshots',
                        ['transaction_type', 'transaction_id'])
        op.create_index('idx_snapshot_completed_at', 'transaction_snapshots',
                        ['completed_at'])

    # 5. Kolom deleted_at di officers (soft delete)
    if not _has_column(conn, "officers", "deleted_at"):
        op.add_column('officers',
                      sa.Column('deleted_at', sa.DateTime, nullable=True,
                                comment='Timestamp saat petugas dihapus (soft delete)'))

    # 6. Kolom deleted_at di inventory_components (soft delete)
    if not _has_column(conn, "inventory_components", "deleted_at"):
        op.add_column('inventory_components',
                      sa.Column('deleted_at', sa.DateTime, nullable=True,
                                comment='Timestamp saat unit dihapus (soft delete)'))

    # 7. Kolom reference_path di activity_logs (link transaksi terkait)
    if not _has_column(conn, "activity_logs", "reference_path"):
        op.add_column('activity_logs',
                      sa.Column('reference_path', sa.String(255), nullable=True,
                                comment='Path frontend untuk navigasi ke transaksi terkait'))


def downgrade() -> None:
    conn = op.get_bind()

    if _has_column(conn, "activity_logs", "reference_path"):
        op.drop_column('activity_logs', 'reference_path')

    if _has_column(conn, "inventory_components", "deleted_at"):
        op.drop_column('inventory_components', 'deleted_at')

    if _has_column(conn, "officers", "deleted_at"):
        op.drop_column('officers', 'deleted_at')

    if _has_table(conn, "transaction_snapshots"):
        op.drop_table('transaction_snapshots')

    if _has_column(conn, "returns", "daily_sequence"):
        op.drop_column('returns', 'daily_sequence')
    if _has_column(conn, "returns", "transaction_number"):
        op.drop_constraint('uq_return_transaction_number', 'returns', type_='unique')
        op.drop_column('returns', 'transaction_number')

    if _has_column(conn, "borrow_transactions", "daily_sequence"):
        op.drop_column('borrow_transactions', 'daily_sequence')
    if _has_column(conn, "borrow_transactions", "transaction_number"):
        op.drop_constraint('uq_borrow_transaction_number', 'borrow_transactions', type_='unique')
        op.drop_column('borrow_transactions', 'transaction_number')

    if _has_table(conn, "transaction_counters"):
        op.drop_table('transaction_counters')
