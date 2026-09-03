"""translate_status_values_to_english

Revision ID: z2a3b4c5d6e7
Revises: zz1a2b3c4d5e
Create Date: 2026-08-27 00:00:00.000000

Mengubah seluruh nilai status yang tersimpan di database dari Bahasa Indonesia
ke Bahasa Inggris. Ini hanya memengaruhi data internal — tampilan frontend tetap
Bahasa Indonesia (diterjemahkan via STATUS_LABELS di frontend).

Mapping:
- borrow_transactions.status : Menunggu→Pending, Dipinjam→Borrowed,
  Dikembalikan→Returned, Dibatalkan→Cancelled
- returns.status              : Menunggu→Pending, Selesai→Completed, Dibatalkan→Cancelled
- borrow_extensions.status    : Menunggu→Pending, Disetujui→Approved, Ditolak→Rejected
- handovers.status            : Dilimpahkan→Transferred, Dibatalkan→Cancelled (Draft tetap)
- inventory_status.status_name: Ditahan→On Hold, Dihapuskan→Deleted, Dilimpahkan→Transferred
- return_details.condition    : Baik→Good, Rusak→Damaged
- return_detail_items.condition: Baik→Good, Rusak→Damaged
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'z2a3b4c5d6e7'
down_revision: Union[str, None] = 'zz1a2b3c4d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # borrow_transactions.status
    op.execute("UPDATE borrow_transactions SET status = 'Pending' WHERE status = 'Menunggu'")
    op.execute("UPDATE borrow_transactions SET status = 'Borrowed' WHERE status = 'Dipinjam'")
    op.execute("UPDATE borrow_transactions SET status = 'Returned' WHERE status = 'Dikembalikan'")
    op.execute("UPDATE borrow_transactions SET status = 'Cancelled' WHERE status = 'Dibatalkan'")

    # returns.status
    op.execute("UPDATE returns SET status = 'Pending' WHERE status = 'Menunggu'")
    op.execute("UPDATE returns SET status = 'Completed' WHERE status = 'Selesai'")
    op.execute("UPDATE returns SET status = 'Cancelled' WHERE status = 'Dibatalkan'")

    # borrow_extensions.status
    op.execute("UPDATE borrow_extensions SET status = 'Pending' WHERE status = 'Menunggu'")
    op.execute("UPDATE borrow_extensions SET status = 'Approved' WHERE status = 'Disetujui'")
    op.execute("UPDATE borrow_extensions SET status = 'Rejected' WHERE status = 'Ditolak'")

    # handovers.status (Draft tetap)
    op.execute("UPDATE handovers SET status = 'Transferred' WHERE status = 'Dilimpahkan'")
    op.execute("UPDATE handovers SET status = 'Cancelled' WHERE status = 'Dibatalkan'")

    # inventory_status.status_name (lookup)
    op.execute("UPDATE inventory_status SET status_name = 'On Hold' WHERE status_name = 'Ditahan'")
    op.execute("UPDATE inventory_status SET status_name = 'Deleted' WHERE status_name = 'Dihapuskan'")
    op.execute("UPDATE inventory_status SET status_name = 'Transferred' WHERE status_name = 'Dilimpahkan'")

    # return_details.condition
    op.execute("UPDATE return_details SET `condition` = 'Good' WHERE `condition` IN ('Baik', 'Bagus', 'Normal')")
    op.execute("UPDATE return_details SET `condition` = 'Damaged' WHERE `condition` IN ('Rusak', 'Rusak Ringan', 'Rusak Berat')")

    # return_detail_items.condition
    op.execute("UPDATE return_detail_items SET `condition` = 'Good' WHERE `condition` IN ('Baik', 'Bagus', 'Normal')")
    op.execute("UPDATE return_detail_items SET `condition` = 'Damaged' WHERE `condition` IN ('Rusak', 'Rusak Ringan', 'Rusak Berat')")


def downgrade() -> None:
    # Kembalikan ke Bahasa Indonesia (jika perlu rollback)
    op.execute("UPDATE borrow_transactions SET status = 'Menunggu' WHERE status = 'Pending'")
    op.execute("UPDATE borrow_transactions SET status = 'Dipinjam' WHERE status = 'Borrowed'")
    op.execute("UPDATE borrow_transactions SET status = 'Dikembalikan' WHERE status = 'Returned'")
    op.execute("UPDATE borrow_transactions SET status = 'Dibatalkan' WHERE status = 'Cancelled'")

    op.execute("UPDATE returns SET status = 'Menunggu' WHERE status = 'Pending'")
    op.execute("UPDATE returns SET status = 'Selesai' WHERE status = 'Completed'")
    op.execute("UPDATE returns SET status = 'Dibatalkan' WHERE status = 'Cancelled'")

    op.execute("UPDATE borrow_extensions SET status = 'Menunggu' WHERE status = 'Pending'")
    op.execute("UPDATE borrow_extensions SET status = 'Disetujui' WHERE status = 'Approved'")
    op.execute("UPDATE borrow_extensions SET status = 'Ditolak' WHERE status = 'Rejected'")

    op.execute("UPDATE handovers SET status = 'Dilimpahkan' WHERE status = 'Transferred'")
    op.execute("UPDATE handovers SET status = 'Dibatalkan' WHERE status = 'Cancelled'")

    op.execute("UPDATE inventory_status SET status_name = 'Ditahan' WHERE status_name = 'On Hold'")
    op.execute("UPDATE inventory_status SET status_name = 'Dihapuskan' WHERE status_name = 'Deleted'")
    op.execute("UPDATE inventory_status SET status_name = 'Dilimpahkan' WHERE status_name = 'Transferred'")

    op.execute("UPDATE return_details SET `condition` = 'Baik' WHERE `condition` = 'Good'")
    op.execute("UPDATE return_details SET `condition` = 'Rusak' WHERE `condition` = 'Damaged'")

    op.execute("UPDATE return_detail_items SET `condition` = 'Baik' WHERE `condition` = 'Good'")
    op.execute("UPDATE return_detail_items SET `condition` = 'Rusak' WHERE `condition` = 'Damaged'")
