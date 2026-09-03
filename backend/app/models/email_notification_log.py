from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class EmailNotificationLog(Base):
    __tablename__ = "email_notification_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_id = Column(BigInteger, ForeignKey("borrow_transactions.id", ondelete="CASCADE"), nullable=True,
                            comment="ID transaksi peminjaman terkait (bisa null untuk test email)")
    admin_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
                           comment="ID user admin penerima")
    recipient_email = Column(String(100), nullable=False, comment="Alamat email penerima")
    notification_type = Column(String(50), nullable=False,
                               comment="Jenis notifikasi: h_minus_2, due_date, overdue, manual, test")
    subject = Column(String(255), nullable=False, comment="Subjek email")
    status = Column(String(20), nullable=False, default="success", comment="Status: success / failed")
    error_message = Column(Text, nullable=True, comment="Pesan error jika pengiriman gagal")
    sent_at = Column(DateTime, server_default=func.now(), nullable=False, comment="Waktu pengiriman")

    borrow_transaction = relationship("BorrowTransaction", lazy="selectin")
    admin_user = relationship("User", lazy="selectin")

    def __repr__(self):
        return f"<EmailNotificationLog(id={self.id}, type='{self.notification_type}', to='{self.recipient_email}', status='{self.status}')>"
