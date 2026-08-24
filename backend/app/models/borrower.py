from sqlalchemy import BigInteger, Column, DateTime, Enum, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import BorrowerType


class Borrower(Base):
    __tablename__ = "borrowers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    borrower_type = Column(Enum(BorrowerType), nullable=False)
    borrower_name = Column(String(100))
    institution = Column(String(150))
    phone = Column(String(20))
    address = Column(Text)
    nip = Column(String(30), nullable=True, unique=True)
    email = Column(String(100), nullable=True, unique=True)
    position = Column(String(100), nullable=True, comment="Jabatan peminjam")
    deleted_at = Column(DateTime, nullable=True, comment="Timestamp saat peminjam dihapus (soft delete)")

    borrow_transactions = relationship("BorrowTransaction", back_populates="borrower", lazy="selectin")

    def __repr__(self):
        return f"<Borrower(id={self.id}, name='{self.borrower_name}', type='{self.borrower_type}')>"