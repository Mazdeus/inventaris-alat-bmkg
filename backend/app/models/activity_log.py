from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    activity = Column(String(255), nullable=False)
    reference_table = Column(String(50))
    reference_id = Column(BigInteger)
    ip_address = Column(String(45), comment="IP address pengguna")
    user_agent = Column(String(255), comment="User agent browser/aplikasi")
    extra_data = Column(Text, comment="Detail tambahan (JSON)")
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    user = relationship("User", back_populates="activity_logs", lazy="selectin")

    def __repr__(self):
        return f"<ActivityLog(id={self.id}, activity='{self.activity[:30]}...')>"