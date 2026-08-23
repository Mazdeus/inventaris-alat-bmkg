from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Return(Base):
    __tablename__ = "returns"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    borrow_id = Column(BigInteger, ForeignKey("borrow_transactions.id"), nullable=False, unique=True)
    received_by = Column(BigInteger, ForeignKey("officers.id", ondelete="SET NULL"), nullable=True, comment="ID petugas yang menerima barang kembali")
    return_date = Column(Date, nullable=False)
    photo = Column(String(255), nullable=True, comment="Path foto dokumentasi pengembalian")
    status = Column(String(50), nullable=False, default="Menunggu", comment="Status: Menunggu / Selesai / Dibatalkan")
    signed_document = Column(String(255), nullable=True, comment="Path dokumen pengembalian tertandatangan")
    late_reason = Column(Text, nullable=True, comment="Alasan keterlambatan pengembalian")
    verified_at = Column(DateTime, nullable=True, comment="Waktu verifikasi oleh admin")

    borrow_transaction = relationship("BorrowTransaction", back_populates="return_", lazy="selectin")
    officer = relationship("Officer", back_populates="returns", lazy="selectin")
    return_details = relationship("ReturnDetail", back_populates="return_", lazy="selectin")

    def __repr__(self):
        return f"<Return(id={self.id}, borrow_id={self.borrow_id}, status='{self.status}')>"