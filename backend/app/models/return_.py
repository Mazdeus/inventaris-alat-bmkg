from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Return(Base):
    __tablename__ = "returns"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_number = Column(String(30), unique=True, nullable=True,
                                comment="Nomor transaksi unik format KB-YYYYMMDDNNN")
    daily_sequence = Column(Integer, nullable=True,
                            comment="Nomor urut harian (reset per hari)")
    borrow_id = Column(BigInteger, ForeignKey("borrow_transactions.id"), nullable=False, unique=True,
                       comment="ID transaksi peminjaman asal")
    received_by = Column(BigInteger, ForeignKey("officers.id", ondelete="SET NULL"), nullable=True, comment="ID petugas yang menerima barang kembali")
    return_date = Column(Date, nullable=False)
    photo = Column(String(255), nullable=True, comment="Path foto dokumentasi pengembalian")
    status = Column(String(50), nullable=False, default="Pending", comment="Status: Pending / Completed / Cancelled")
    signed_document = Column(String(255), nullable=True, comment="Path dokumen pengembalian tertandatangan")
    late_reason = Column(Text, nullable=True, comment="Alasan keterlambatan pengembalian")
    verified_at = Column(DateTime, nullable=True, comment="Waktu verifikasi oleh admin")

    borrow_transaction = relationship("BorrowTransaction", back_populates="return_", lazy="selectin")
    officer = relationship("Officer", back_populates="returns", lazy="selectin")
    return_details = relationship("ReturnDetail", back_populates="return_", lazy="selectin")

    def __repr__(self):
        return f"<Return(id={self.id}, tx='{self.transaction_number}', borrow_id={self.borrow_id}, status='{self.status}')>"