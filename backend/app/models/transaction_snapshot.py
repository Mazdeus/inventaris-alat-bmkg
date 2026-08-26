"""TransactionSnapshot — arsip data transaksi selesai (snapshot JSON)."""
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, JSON, String, func

from app.core.database import Base


class TransactionSnapshot(Base):
    __tablename__ = "transaction_snapshots"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_type = Column(String(50), nullable=False,
                              comment="Jenis: 'borrow' / 'return' / 'handover' / 'maintenance'")
    transaction_id = Column(BigInteger, nullable=False,
                            comment="ID asli di tabel transaksi terkait")
    snapshot_data = Column(JSON, nullable=False,
                           comment="Snapshot data transaksi saat selesai (JSON)")
    completed_at = Column(DateTime, nullable=False,
                          comment="Waktu transaksi selesai/dibatalkan")
    archived_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"),
                         nullable=True, comment="User yang menyelesaikan/mengarsipkan")
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<TransactionSnapshot(type='{self.transaction_type}', id={self.transaction_id})>"
