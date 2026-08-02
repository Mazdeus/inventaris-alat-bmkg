from sqlalchemy import BigInteger, Column, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    role_name = Column(String(50), unique=True, nullable=False)

    users = relationship("User", back_populates="role", lazy="selectin")

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.role_name}')>"