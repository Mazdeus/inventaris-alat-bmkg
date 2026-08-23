"""rename_return_status_menunggu

Revision ID: a2b3c4d5e6f7
Revises: z1a2b3c4d5e6
Create Date: 2026-08-19 00:00:00.000000

Mengubah status pengembalian 'Menunggu Verifikasi' menjadi 'Menunggu'.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = 'z1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE returns SET status = 'Menunggu' WHERE status = 'Menunggu Verifikasi'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE returns SET status = 'Menunggu Verifikasi' WHERE status = 'Menunggu'"
    )
