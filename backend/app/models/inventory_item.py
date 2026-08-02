from sqlalchemy import BigInteger, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class InventoryItem(Base):
    """Tabel untuk tracking barang individual (per fisik, bukan per jenis)."""
    __tablename__ = "inventory_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    inventory_component_id = Column(BigInteger, ForeignKey("inventory_components.id"), nullable=False)
    serial_number = Column(String(100), nullable=True, comment="Serial number per barang fisik")
    status_id = Column(BigInteger, ForeignKey("inventory_status.id"), nullable=False, default=1)
    notes = Column(Text, nullable=True)

    component = relationship("InventoryComponent", back_populates="items", lazy="selectin")
    status = relationship("InventoryStatus", lazy="selectin")
    borrow_detail_items = relationship("BorrowDetailItem", back_populates="inventory_item", lazy="selectin")
    return_detail_items = relationship("ReturnDetailItem", back_populates="inventory_item", lazy="selectin")

    def __repr__(self):
        return f"<InventoryItem(id={self.id}, sn='{self.serial_number}')>"
