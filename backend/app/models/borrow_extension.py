"""BorrowExtension — perpanjangan masa peminjaman."""
from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class BorrowExtension(Base):
    __tablename__ = "borrow_extensions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    borrow_id = Column(BigInteger, ForeignKey("borrow_transactions.id", ondelete="CASCADE"), nullable=False)
    requested_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    requested_return_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=True, comment="Alasan perpanjangan")
    status = Column(String(50), nullable=False, default="Menunggu", comment="Menunggu / Disetujui / Ditolak")
    approved_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    borrow_transaction = relationship("BorrowTransaction", back_populates="extensions", lazy="selectin")
    requester = relationship("User", foreign_keys=[requested_by], back_populates="requested_extensions", lazy="selectin")
    approver = relationship("User", foreign_keys=[approved_by], back_populates="approved_extensions", lazy="selectin")

    def __repr__(self):
        return f"<BorrowExtension(id={self.id}, borrow={self.borrow_id}, status='{self.status}')>"
