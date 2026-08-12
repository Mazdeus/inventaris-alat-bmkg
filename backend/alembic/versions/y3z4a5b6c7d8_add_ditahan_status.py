"""add_ditahan_status

Revision ID: y3z4a5b6c7d8
Revises: x2y3z4a5b6c7
Create Date: 2026-08-12 00:00:00.000000

Menambahkan status "Ditahan" (Reserved) ke inventory_status untuk barang
yang sedang dalam transaksi pending (peminjaman Menunggu, handover Draft).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'y3z4a5b6c7d8'
down_revision: Union[str, None] = 'x2y3z4a5b6c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "INSERT INTO inventory_status (id, status_name) VALUES (7, 'Ditahan') "
        "ON DUPLICATE KEY UPDATE status_name = 'Ditahan'"
    )


def downgrade() -> None:
    op.execute("DELETE FROM inventory_status WHERE id = 7")
