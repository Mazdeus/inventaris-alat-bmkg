from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class BorrowTransaction(Base):
    __tablename__ = "borrow_transactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_number = Column(String(11), unique=True, nullable=True,
                                comment="Nomor transaksi unik format YYYYMMDDNNN")
    daily_sequence = Column(Integer, nullable=True,
                            comment="Nomor urut harian (reset per hari)")
    borrower_id = Column(BigInteger, ForeignKey("borrowers.id"), nullable=False)
    issued_by = Column(BigInteger, ForeignKey("officers.id", ondelete="SET NULL"), nullable=True, comment="ID petugas yang mengeluarkan barang")
    borrow_date = Column(Date, nullable=False)
    expected_return_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False, default="Menunggu", comment="Menunggu / Dipinjam / Dikembalikan / Dibatalkan")
    photo = Column(String(255), nullable=True, comment="Path foto dokumentasi peminjaman")
    signed_document = Column(String(255), nullable=True, comment="Path dokumen yang sudah ditandatangani")
    item_description = Column(Text, nullable=True, comment="Deskripsi barang yang dipinjam")
    purpose = Column(Text, nullable=True, comment="Tujuan peminjaman")
    created_at = Column(DateTime, server_default=func.now())

    borrower = relationship("Borrower", back_populates="borrow_transactions", lazy="selectin")
    officer = relationship("Officer", back_populates="borrow_transactions", lazy="selectin")
    borrow_details = relationship("BorrowDetail", back_populates="borrow_transaction", lazy="selectin")
    return_ = relationship("Return", back_populates="borrow_transaction", uselist=False, lazy="selectin")
    extensions = relationship("BorrowExtension", back_populates="borrow_transaction", lazy="selectin")

    def __repr__(self):
        return f"<BorrowTransaction(id={self.id}, status='{self.status}')>"