"""Officer model — data petugas yang mengeluarkan/menerima barang."""
from sqlalchemy import BigInteger, Boolean, Column, DateTime, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Officer(Base):
    __tablename__ = "officers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    officer_name = Column(String(100), nullable=False)
    nip = Column(String(30), nullable=False, unique=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    institution = Column(String(150), nullable=True, comment="Instansi/unit kerja petugas")
    is_active = Column(Boolean, default=True, server_default=func.true(), nullable=False)
    deleted_at = Column(DateTime, nullable=True, comment="Timestamp saat petugas dihapus (soft delete)")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    borrow_transactions = relationship("BorrowTransaction", back_populates="officer", lazy="selectin")
    returns = relationship("Return", back_populates="officer", lazy="selectin")

    def __repr__(self):
        return f"<Officer(id={self.id}, name='{self.officer_name}')>"
