from sqlalchemy import BigInteger, Column, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class InventoryStatus(Base):
    __tablename__ = "inventory_status"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    status_name = Column(String(50), unique=True, nullable=False)

    inventory_components = relationship("InventoryComponent", back_populates="status", lazy="selectin")

    def __repr__(self):
        return f"<InventoryStatus(id={self.id}, name='{self.status_name}')>"