"""Handover — transaksi pelimpahan barang ke UPT."""
from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Handover(Base):
    __tablename__ = "handovers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_number = Column(String(20), unique=True, nullable=True, comment="Nomor transaksi pelimpahan PL-YYYYMMDDNNN")
    daily_sequence = Column(Integer, nullable=True, comment="Nomor urut transaksi harian")
    upt_receiver = Column(String(100), nullable=False, comment="UPT penerima barang")
    upt_id = Column(BigInteger, ForeignKey("upts.id", ondelete="SET NULL"), nullable=True, comment="ID referensi UPT penerima")
    recipient_name = Column(String(100), nullable=True, comment="Nama pihak/petugas penerima di UPT")
    recipient_nip = Column(String(30), nullable=True, comment="NIP pihak/petugas penerima di UPT")
    issued_by = Column(BigInteger, ForeignKey("officers.id", ondelete="SET NULL"),
                       nullable=True, comment="ID petugas yang menyerahkan")
    handover_date = Column(Date, nullable=False, comment="Tanggal pelimpahan")
    status = Column(String(50), nullable=False, default="Draft",
                    comment="Status: Draft / Transferred / Cancelled")
    photo = Column(String(255), nullable=True, comment="Path foto dokumentasi pelimpahan")
    signed_document = Column(String(255), nullable=True, comment="Path dokumen tertandatangan")
    notes = Column(Text, nullable=True, comment="Catatan pelimpahan")
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True, comment="Waktu pelimpahan selesai")

    upt = relationship("Upt", back_populates="handovers", lazy="selectin")
    officer = relationship("Officer", lazy="selectin")
    items = relationship("HandoverItem", back_populates="handover", lazy="selectin",
                         cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Handover(id={self.id}, upt='{self.upt_receiver}', status='{self.status}')>"
