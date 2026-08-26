"""TransactionNumberService — generate nomor transaksi harian (YYYYMMDDNNN).

Menggunakan pola atomic counter MySQL (INSERT ... ON DUPLICATE KEY UPDATE
dengan LAST_INSERT_ID) agar aman dari race condition saat beberapa request
bersamaan membuat transaksi di tanggal yang sama.
"""
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session


def generate_transaction_number(db: Session, counter_type: str) -> tuple[str, int]:
    """Generate nomor transaksi baru untuk tanggal hari ini.

    Returns:
        (transaction_number, daily_sequence) — misal ("20260826001", 1)
    """
    today = date.today()

    db.execute(
        text(
            "INSERT INTO transaction_counters (counter_type, counter_date, last_sequence) "
            "VALUES (:counter_type, :counter_date, 1) "
            "ON DUPLICATE KEY UPDATE last_sequence = LAST_INSERT_ID(last_sequence + 1)"
        ),
        {"counter_type": counter_type, "counter_date": today},
    )

    seq = int(db.execute(text("SELECT LAST_INSERT_ID()")).scalar() or 1)
    transaction_number = f"{today.strftime('%Y%m%d')}{seq:03d}"
    return transaction_number, seq
