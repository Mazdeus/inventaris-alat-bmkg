"""UPT (Unit Pelaksana Teknis) model — data kantor / stasiun UPT BMKG."""
from sqlalchemy import BigInteger, Boolean, Column, DateTime, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Upt(Base):
    __tablename__ = "upts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False, unique=True, comment="Nama UPT BMKG")
    address = Column(Text, nullable=True, comment="Alamat UPT (opsional)")
    phone = Column(String(50), nullable=True, comment="Kontak UPT (opsional)")
    is_active = Column(Boolean, default=True, server_default=func.true(), nullable=False)
    deleted_at = Column(DateTime, nullable=True, comment="Timestamp saat UPT dihapus (soft delete)")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relasi ke pelimpahan
    handovers = relationship("Handover", back_populates="upt", lazy="selectin")

    def __repr__(self):
        return f"<Upt(id={self.id}, name='{self.name}')>"
