from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class ReturnDetail(Base):
    __tablename__ = "return_details"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    return_id = Column(BigInteger, ForeignKey("returns.id"), nullable=False)
    inventory_component_id = Column(BigInteger, ForeignKey("inventory_components.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    condition = Column(String(50), nullable=False)
    notes = Column(Text)

    return_ = relationship("Return", back_populates="return_details", lazy="selectin")
    inventory_component = relationship("InventoryComponent", back_populates="return_details", lazy="selectin")
    return_detail_items = relationship("ReturnDetailItem", back_populates="return_detail", lazy="selectin",
                                       cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ReturnDetail(id={self.id}, qty={self.quantity})>"