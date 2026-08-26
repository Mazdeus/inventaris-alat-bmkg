"""TransactionCounter — counter nomor transaksi harian (atomic)."""
from sqlalchemy import BigInteger, Column, Date, Integer, String, UniqueConstraint

from app.core.database import Base


class TransactionCounter(Base):
    __tablename__ = "transaction_counters"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    counter_type = Column(String(50), nullable=False, comment="Jenis counter: 'borrow' / 'return'")
    counter_date = Column(Date, nullable=False, comment="Tanggal counter (reset harian)")
    last_sequence = Column(Integer, nullable=False, default=0, comment="Nomor urut terakhir pada tanggal tersebut")

    __table_args__ = (
        UniqueConstraint("counter_type", "counter_date", name="uq_transaction_counter"),
    )

    def __repr__(self):
        return f"<TransactionCounter(type='{self.counter_type}', date={self.counter_date}, seq={self.last_sequence})>"
