"""HandoverItem — barang yang dilimpahkan dalam satu transaksi handover."""
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class HandoverItem(Base):
    __tablename__ = "handover_items"
    __table_args__ = (
        UniqueConstraint('handover_id', 'inventory_item_id', name='uq_handover_item'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    handover_id = Column(BigInteger, ForeignKey("handovers.id", ondelete="CASCADE"), nullable=False)
    inventory_item_id = Column(BigInteger, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    handover = relationship("Handover", back_populates="items", lazy="selectin")
    inventory_item = relationship("InventoryItem", lazy="selectin")

    def __repr__(self):
        return f"<HandoverItem(id={self.id}, handover={self.handover_id}, item={self.inventory_item_id})>"
