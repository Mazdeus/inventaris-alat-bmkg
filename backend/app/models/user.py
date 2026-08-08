from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    role_id = Column(BigInteger, ForeignKey("roles.id"), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True, comment="Nomor telepon admin")
    email = Column(String(100), nullable=True, unique=True, comment="Email admin")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    role = relationship("Role", back_populates="users", lazy="selectin")
    activity_logs = relationship("ActivityLog", back_populates="user", lazy="selectin")
    requested_extensions = relationship(
        "BorrowExtension", foreign_keys="BorrowExtension.requested_by",
        back_populates="requester", lazy="selectin",
    )
    approved_extensions = relationship(
        "BorrowExtension", foreign_keys="BorrowExtension.approved_by",
        back_populates="approver", lazy="selectin",
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"