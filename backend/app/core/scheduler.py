"""Background Task Scheduler menggunakan APScheduler (AsyncIOScheduler)."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging_config import get_logger

logger = get_logger()
scheduler = AsyncIOScheduler()


async def scheduled_daily_due_reminder_job():
    """Fungsi job otomatis harian untuk memindai dan mengirim email alert ke Admin."""
    logger.info("⏰ Memulai eksekusi jadwal cron pengingat tenggat peminjaman harian...")
    db = SessionLocal()
    try:
        from app.services.reminder_service import scan_and_send_due_reminders
        result = await scan_and_send_due_reminders(db, force=False)
        logger.info("⏰ Hasil cron pengingat harian: %s", result)
    except Exception as e:
        logger.error("⏰ Terjadi error pada cron pengingat harian: %s", e, exc_info=True)
    finally:
        db.close()


def start_scheduler():
    """Memulai scheduler background task saat server FastAPI startup."""
    if not settings.SMTP_ENABLED:
        logger.info("Scheduler pengingat email tidak diaktifkan karena SMTP_ENABLED=False.")
        return

    try:
        # Tambahkan cron job harian pada jam & menit yang ditentukan di .env
        cron_trigger = CronTrigger(
            hour=settings.EMAIL_REMINDER_CRON_HOUR,
            minute=settings.EMAIL_REMINDER_CRON_MINUTE,
        )
        scheduler.add_job(
            scheduled_daily_due_reminder_job,
            trigger=cron_trigger,
            id="daily_due_reminder_job",
            name="Daily Borrow Due Date Reminder to Admin",
            replace_existing=True,
        )
        scheduler.start()
        logger.info(
            "Scheduler pengingat email aktif: berjalan setiap hari pukul %02d:%02d WIB.",
            settings.EMAIL_REMINDER_CRON_HOUR,
            settings.EMAIL_REMINDER_CRON_MINUTE,
        )
    except Exception as e:
        logger.error("Gagal memulai scheduler background task: %s", e, exc_info=True)


def stop_scheduler():
    """Menghentikan scheduler saat server FastAPI shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler pengingat email telah dihentikan.")
