from datetime import date

from sqlalchemy.orm import Session

from app.models.transaction_counter import TransactionCounter

PREFIX_MAP = {
    "borrow": "PJ-",
    "return": "KB-",
    "handover": "PL-",
    "maintenance": "PM-",
}


def generate_transaction_number(db: Session, counter_type: str) -> tuple[str, int]:
    """Generate nomor transaksi baru untuk tanggal hari ini.

    Menggunakan row-level locking (`with_for_update()`) agar counter
    benar-benar aman dari race condition dan independen per modul.

    Returns:
        (transaction_number, daily_sequence) — misal ("PJ-20260902001", 1)
    """
    today = date.today()
    prefix = PREFIX_MAP.get(counter_type, "")

    row = (
        db.query(TransactionCounter)
        .filter(
            TransactionCounter.counter_type == counter_type,
            TransactionCounter.counter_date == today,
        )
        .with_for_update()
        .first()
    )

    if row:
        row.last_sequence += 1
        seq = row.last_sequence
    else:
        seq = 1
        row = TransactionCounter(
            counter_type=counter_type,
            counter_date=today,
            last_sequence=1,
        )
        db.add(row)

    db.flush()
    transaction_number = f"{prefix}{today.strftime('%Y%m%d')}{seq:03d}"
    return transaction_number, seq


