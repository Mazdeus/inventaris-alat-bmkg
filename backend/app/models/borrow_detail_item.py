"""BorrowDetailItem — tracking per item fisik yang dipilih dalam satu borrow_detail."""
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class BorrowDetailItem(Base):
    __tablename__ = "borrow_detail_items"
    __table_args__ = (
        UniqueConstraint('borrow_detail_id', 'inventory_item_id', name='uq_borrow_detail_item'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    borrow_detail_id = Column(BigInteger, ForeignKey("borrow_details.id", ondelete="CASCADE"), nullable=False)
    inventory_item_id = Column(BigInteger, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    borrow_detail = relationship("BorrowDetail", back_populates="borrow_detail_items", lazy="selectin")
    inventory_item = relationship("InventoryItem", back_populates="borrow_detail_items", lazy="selectin")

    def __repr__(self):
        return f"<BorrowDetailItem(id={self.id}, detail={self.borrow_detail_id}, item={self.inventory_item_id})>"
