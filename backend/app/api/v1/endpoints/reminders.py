"""Endpoints REST API untuk Notifikasi Email & Alert Tenggat Peminjaman."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.core.scheduler import scheduler
from app.models.email_notification_log import EmailNotificationLog
from app.models.user import User
from app.services.reminder_service import (
    scan_and_send_due_reminders,
    send_single_transaction_alert,
    test_smtp_connection,
)

router = APIRouter(prefix="/api/v1/reminders", tags=["Reminders & Email Alerts"])


class TestSmtpRequest(BaseModel):
    to_email: Optional[str] = None



@router.get("/status")
def get_email_reminder_status(
    current_user: User = Depends(get_current_admin_user),
):
    """Melihat status konfigurasi SMTP dan scheduler background task."""
    has_pwd = bool(settings.SMTP_PASSWORD and len(settings.SMTP_PASSWORD) > 0)
    masked_pwd = ("*" * 12 + settings.SMTP_PASSWORD[-4:]) if (has_pwd and len(settings.SMTP_PASSWORD) >= 4) else ("*" * 8 if has_pwd else None)

    return {
        "status": "success",
        "data": {
            "smtp_enabled": settings.SMTP_ENABLED,
            "smtp_host": settings.SMTP_HOST,
            "smtp_port": settings.SMTP_PORT,
            "smtp_user": settings.SMTP_USER,
            "smtp_from_email": settings.SMTP_FROM_EMAIL or settings.SMTP_USER,
            "smtp_from_name": settings.SMTP_FROM_NAME,
            "has_password": has_pwd,
            "masked_password": masked_pwd,
            "cron_schedule": f"{settings.EMAIL_REMINDER_CRON_HOUR:02d}:{settings.EMAIL_REMINDER_CRON_MINUTE:02d} WIB",
            "scheduler_running": scheduler.running if scheduler else False,
        },
    }


@router.post("/test-smtp")
async def test_smtp_endpoint(
    req: TestSmtpRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Menguji koneksi SMTP dengan mengirimkan email uji coba ke alamat email admin."""
    target_email = req.to_email or current_user.email
    if not target_email:
        raise HTTPException(
            status_code=400,
            detail="Alamat email tujuan pengujian belum ditentukan dan akun admin ini belum memiliki email.",
        )

    result = await test_smtp_connection(
        to_email=str(target_email),
        db=db,
        admin_user_id=current_user.id,
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return {
        "status": "success",
        "message": result["message"],
        "data": result,
    }


@router.post("/trigger-check")
async def trigger_due_check_endpoint(
    force: bool = Query(False, description="Kirim ulang email meski sudah pernah terkirim hari ini"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Memicu pemindaian seluruh transaksi peminjaman (H-2, Hari-H, Overdue) dan mengirimkan alert ke admin secara instan."""
    result = await scan_and_send_due_reminders(db=db, force=force)
    return {
        "status": "success",
        "message": "Pengecekan dan pengiriman alert tenggat selesai dieksekusi.",
        "data": result,
    }


@router.post("/send-transaction/{transaction_id}")
async def send_transaction_alert_endpoint(
    transaction_id: int,
    notification_type: str = Query("manual", description="h_minus_2 / due_date / overdue / manual"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Mengirim email alert untuk transaksi peminjaman tertentu ke Admin."""
    result = await send_single_transaction_alert(
        db=db,
        transaction_id=transaction_id,
        notification_type=notification_type,
        specific_admin_id=None,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return {
        "status": "success",
        "message": result["message"],
        "data": result,
    }


@router.get("/logs")
def list_email_logs_endpoint(
    page: int = Query(1, ge=1, description="Halaman"),
    size: int = Query(20, ge=1, le=100, description="Jumlah per halaman"),
    notification_type: Optional[str] = Query(None, description="Filter jenis notifikasi"),
    status: Optional[str] = Query(None, description="Filter status success/failed"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Melihat daftar riwayat notifikasi email yang telah dikirim ke Admin."""
    query = db.query(EmailNotificationLog)

    if notification_type:
        query = query.filter(EmailNotificationLog.notification_type == notification_type)
    if status:
        query = query.filter(EmailNotificationLog.status == status)

    total = query.count()
    offset = (page - 1) * size
    logs = (
        query.order_by(EmailNotificationLog.sent_at.desc())
        .offset(offset)
        .limit(size)
        .all()
    )

    data = []
    for log in logs:
        tx_no = log.borrow_transaction.transaction_number if log.borrow_transaction else None
        borrower_name = log.borrow_transaction.borrower.borrower_name if (log.borrow_transaction and log.borrow_transaction.borrower) else None
        data.append({
            "id": log.id,
            "transaction_id": log.transaction_id,
            "transaction_number": tx_no,
            "borrower_name": borrower_name,
            "admin_user_id": log.admin_user_id,
            "recipient_email": log.recipient_email,
            "notification_type": log.notification_type,
            "subject": log.subject,
            "status": log.status,
            "error_message": log.error_message,
            "sent_at": log.sent_at.isoformat() if log.sent_at else None,
        })

    return {
        "status": "success",
        "message": "Riwayat log email berhasil diambil",
        "data": data,
        "meta": {
            "page": page,
            "size": size,
            "total": total,
            "total_pages": (total + size - 1) // size if total > 0 else 0,
        },
    }
