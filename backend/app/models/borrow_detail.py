from sqlalchemy import BigInteger, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class BorrowDetail(Base):
    __tablename__ = "borrow_details"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    borrow_id = Column(BigInteger, ForeignKey("borrow_transactions.id"), nullable=False)
    inventory_component_id = Column(BigInteger, ForeignKey("inventory_components.id"), nullable=False)
    quantity = Column(Integer, nullable=False)

    borrow_transaction = relationship("BorrowTransaction", back_populates="borrow_details", lazy="selectin")
    inventory_component = relationship("InventoryComponent", back_populates="borrow_details", lazy="selectin")
    borrow_detail_items = relationship("BorrowDetailItem", back_populates="borrow_detail", lazy="selectin",
                                       cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BorrowDetail(id={self.id}, qty={self.quantity})>"