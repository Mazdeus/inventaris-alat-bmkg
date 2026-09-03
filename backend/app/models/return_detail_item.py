"""ReturnDetailItem — tracking kondisi per barang fisik dalam pengembalian."""
from sqlalchemy import BigInteger, Column, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class ReturnDetailItem(Base):
    __tablename__ = "return_detail_items"
    __table_args__ = (
        UniqueConstraint('return_detail_id', 'inventory_item_id', name='uq_return_detail_item'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    return_detail_id = Column(BigInteger, ForeignKey("return_details.id", ondelete="CASCADE"), nullable=False)
    inventory_item_id = Column(BigInteger, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False)
    condition = Column(String(50), nullable=False, comment="Kondisi: Good / Damaged")
    notes = Column(Text, nullable=True, comment="Catatan per barang")

    return_detail = relationship("ReturnDetail", back_populates="return_detail_items", lazy="selectin")
    inventory_item = relationship("InventoryItem", back_populates="return_detail_items", lazy="selectin")

    def __repr__(self):
        return f"<ReturnDetailItem(id={self.id}, item={self.inventory_item_id}, cond='{self.condition}')>"
