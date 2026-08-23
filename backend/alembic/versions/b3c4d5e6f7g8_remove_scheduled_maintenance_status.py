"""remove_scheduled_maintenance_status

Revision ID: b3c4d5e6f7g8
Revises: a2b3c4d5e6f7
Create Date: 2026-08-19 00:00:00.000000

Menghapus status "Scheduled" (Terjadwal) dari maintenance karena tidak ada
perbedaan perilaku dengan "In Progress" (barang langsung berstatus Maintenance
saat perawatan dibuat). Data lama dengan status Scheduled diubah menjadi In Progress.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'b3c4d5e6f7g8'
down_revision: Union[str, None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE maintenance SET status = 'In Progress' WHERE status = 'Scheduled'"
    )


def downgrade() -> None:
    # Tidak bisa membedakan data mana yang sebelumnya Scheduled — no-op.
    pass
