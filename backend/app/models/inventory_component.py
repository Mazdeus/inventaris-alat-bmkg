from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class InventoryComponent(Base):
    __tablename__ = "inventory_components"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    status_id = Column(BigInteger, ForeignKey("inventory_status.id"), nullable=False)
    item_name = Column(String(100), nullable=False)
    brand = Column(String(100))
    model = Column(String(100))
    serial_number = Column(String(100))
    procurement_year = Column(SmallInteger)
    procurement_month = Column(Integer, nullable=False, default=1, server_default="1", comment="Bulan pengadaan (1-12)")
    supplier = Column(String(150))
    total_quantity = Column(Integer, nullable=False)
    specifications = Column(Text, nullable=True, comment="Spesifikasi teknis komponen")
    photo_url = Column(String(500), nullable=True, comment="URL absolut foto (relative to localhost)")
    photo_path = Column(String(500), nullable=True, comment="Path absolut filesystem foto")
    division = Column(String(50), nullable=False, server_default="", comment="Divisi/Seksi: Gempa Bumi, Tsunami, Percepatan Tanah")
    notes = Column(Text)
    deleted_at = Column(DateTime, nullable=True, comment="Timestamp saat unit dihapus (soft delete)")
    status = relationship("InventoryStatus", back_populates="inventory_components", lazy="selectin")
    borrow_details = relationship("BorrowDetail", back_populates="inventory_component", lazy="selectin")
    return_details = relationship("ReturnDetail", back_populates="inventory_component", lazy="selectin")
    maintenance_records = relationship("Maintenance", back_populates="inventory_component", lazy="selectin")
    items = relationship("InventoryItem", back_populates="component", lazy="selectin")

    def __repr__(self):
        return f"<InventoryComponent(id={self.id}, name='{self.item_name}')>"