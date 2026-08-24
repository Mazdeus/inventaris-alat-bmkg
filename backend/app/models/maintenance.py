from sqlalchemy import BigInteger, Column, Date, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Maintenance(Base):
    __tablename__ = "maintenance"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    inventory_component_id = Column(BigInteger, ForeignKey("inventory_components.id"), nullable=False)
    officer_id = Column(BigInteger, ForeignKey("officers.id", ondelete="SET NULL"), nullable=True,
                        comment="ID petugas yang melakukan pemeliharaan")
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    description = Column(Text)
    status = Column(String(50), nullable=False)

    inventory_component = relationship("InventoryComponent", back_populates="maintenance_records", lazy="selectin")
    officer = relationship("Officer", lazy="selectin")
    maintenance_items = relationship("MaintenanceItem", back_populates="maintenance", lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Maintenance(id={self.id}, status='{self.status}')>"