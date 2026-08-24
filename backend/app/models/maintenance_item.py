"""MaintenanceItem — tracking per barang fisik yang terlibat dalam pemeliharaan."""
from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class MaintenanceItem(Base):
    __tablename__ = "maintenance_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    maintenance_id = Column(BigInteger, ForeignKey("maintenance.id", ondelete="CASCADE"), nullable=False)
    inventory_item_id = Column(BigInteger, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False)
    previous_status_id = Column(BigInteger, ForeignKey("inventory_status.id", ondelete="SET NULL"), nullable=True)

    maintenance = relationship("Maintenance", back_populates="maintenance_items", lazy="selectin")
    inventory_item = relationship("InventoryItem", back_populates="maintenance_items", lazy="selectin")
    previous_status = relationship("InventoryStatus", lazy="selectin")

    def __repr__(self):
        return f"<MaintenanceItem(id={self.id}, maint={self.maintenance_id}, item={self.inventory_item_id})>"
