"""ItemStatusHistory — riwayat perubahan status per barang fisik."""
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ItemStatusHistory(Base):
    __tablename__ = "item_status_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    inventory_item_id = Column(BigInteger, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False)
    inventory_component_id = Column(BigInteger, ForeignKey("inventory_components.id", ondelete="CASCADE"), nullable=False)
    from_status_id = Column(BigInteger, ForeignKey("inventory_status.id", ondelete="SET NULL"), nullable=True)
    to_status_id = Column(BigInteger, ForeignKey("inventory_status.id", ondelete="RESTRICT"), nullable=False)
    source = Column(String(50), nullable=False, comment="RETURN / ADMIN_TOGGLE / MAINTENANCE / DELETE")
    return_id = Column(BigInteger, ForeignKey("returns.id", ondelete="SET NULL"), nullable=True)
    borrow_transaction_id = Column(BigInteger, ForeignKey("borrow_transactions.id", ondelete="SET NULL"), nullable=True)
    maintenance_id = Column(BigInteger, ForeignKey("maintenance.id", ondelete="SET NULL"), nullable=True)
    handover_id = Column(BigInteger, ForeignKey("handovers.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    inventory_item = relationship("InventoryItem", back_populates="status_history", lazy="selectin")
    inventory_component = relationship("InventoryComponent", lazy="selectin")
    from_status = relationship("InventoryStatus", foreign_keys=[from_status_id], lazy="selectin")
    to_status = relationship("InventoryStatus", foreign_keys=[to_status_id], lazy="selectin")
    return_record = relationship("Return", lazy="selectin")
    borrow_transaction = relationship("BorrowTransaction", lazy="selectin")
    maintenance = relationship("Maintenance", lazy="selectin")
    handover = relationship("Handover", lazy="selectin")
    user = relationship("User", lazy="selectin")

    def __repr__(self):
        return f"<ItemStatusHistory(id={self.id}, item={self.inventory_item_id}, {self.source})>"

