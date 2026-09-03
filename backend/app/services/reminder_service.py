"""Layanan Bisnis Pengingat Email & Alert Tenggat Peminjaman (Khusus Admin BMKG)."""
from datetime import date, datetime
from pathlib import Path
import jinja2
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import get_logger
from app.core.mail import send_email_async
from app.models.borrow_transaction import BorrowTransaction
from app.models.email_notification_log import EmailNotificationLog
from app.models.role import Role
from app.models.user import User
from app.services.activity_log_service import ActivityLogService


logger = get_logger()

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "emails"
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=jinja2.select_autoescape(["html", "xml"]),
)


def get_active_admin_users(db: Session) -> list[User]:
    """Mengambil semua pengguna aktif ber-role 'Admin' yang memiliki email valid."""
    admin_users = (
        db.query(User)
        .join(Role, User.role_id == Role.id)
        .filter(
            Role.role_name.ilike("%admin%"),
            User.is_active == True,
            User.email.isnot(None),
            User.email != "",
        )
        .all()
    )
    return admin_users


def format_date_id(dt: date | datetime | None) -> str:
    """Format tanggal Indonesia (DD MMMM YYYY)."""
    if not dt:
        return "-"
    months = [
        "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    return f"{dt.day} {months[dt.month]} {dt.year}"


def prepare_alert_email_content(
    transaction: BorrowTransaction,
    notification_type: str,
    admin_user: User,
) -> tuple[str, str]:
    """Menyiapkan subjek dan konten HTML email alert peminjaman untuk Admin."""
    today = date.today()
    days_diff = (transaction.expected_return_date - today).days

    # Konfigurasi Badge, Subjek, dan Pesan berdasarkan Tipe Notifikasi
    if notification_type == "h_minus_2" or days_diff == 2:
        badge_text = "🟡 PERINGATAN H-2 TENGGAT WAKTU"
        badge_class = "badge-h2"
        headline = f"Peringatan H-2: Peminjaman {transaction.transaction_number or 'Alat'} Segera Jatuh Tempo"
        subject = f"[PERINGATAN H-2] Tenggat Peminjaman {transaction.transaction_number or ''} ({transaction.borrower.borrower_name if transaction.borrower else 'Peminjam'})"
        status_days_desc = "Jatuh tempo dalam 2 hari lagi"
        action_note = "Mohon konfirmasi atau ingatkan peminjam untuk mempersiapkan pengembalian alat sesuai jadwal yang disepakati."

    elif notification_type == "due_date" or days_diff == 0:
        badge_text = "🔵 JATUH TEMPO HARI INI"
        badge_class = "badge-due"
        headline = f"Pemberitahuan: Peminjaman {transaction.transaction_number or 'Alat'} Jatuh Tempo Hari Ini"
        subject = f"[JATUH TEMPO HARI INI] Peminjaman {transaction.transaction_number or ''} ({transaction.borrower.borrower_name if transaction.borrower else 'Peminjam'})"
        status_days_desc = "Jatuh tempo HARI INI"
        action_note = "Harap tunggu konfirmasi kedatangan peminjam untuk proses serah terima pengembalian dan pengecekan fisik kondisi alat."

    elif notification_type == "overdue" or days_diff < 0:
        overdue_days = abs(days_diff)
        badge_text = f"🔴 TERLAMBAT {overdue_days} HARI"
        badge_class = "badge-overdue"
        headline = f"PERINGATAN KETERLAMBATAN: Peminjaman {transaction.transaction_number or 'Alat'} Melewati Batas Waktu"
        subject = f"[TERLAMBAT {overdue_days} HARI] Peminjaman {transaction.transaction_number or ''} ({transaction.borrower.borrower_name if transaction.borrower else 'Peminjam'})"
        status_days_desc = f"Terlambat {overdue_days} hari dari jadwal"
        action_note = "PENTING: Alat belum dikembalikan melewati batas waktu. Segera hubungi peminjam melalui nomor kontak yang tertera untuk meminta pengembalian atau perpanjangan resmi."

    else:
        badge_text = "🟣 NOTIFIKASI PEMINJAMAN ALAT"
        badge_class = "badge-manual"
        headline = f"Informasi Status Peminjaman {transaction.transaction_number or 'Alat'}"
        subject = f"[INFO INVENTARIS] Peminjaman {transaction.transaction_number or ''} - {transaction.borrower.borrower_name if transaction.borrower else 'Peminjam'}"
        status_days_desc = f"Batas: {format_date_id(transaction.expected_return_date)}"
        action_note = "Informasi peminjaman alat BMKG untuk pemantauan sirkulasi inventaris."

    # Kumpulkan rincian barang fisik dan serial numbers
    items_data = []
    total_items = 0
    for idx, detail in enumerate(transaction.borrow_details, start=1):
        comp = detail.inventory_component
        comp_name = comp.item_name if comp else "Alat/Komponen"

        specs = f"{comp.brand or ''} {comp.model or ''}".strip() if comp else ""
        if comp and comp.division:
            specs = f"[{comp.division}] {specs}" if specs else f"[{comp.division}]"

        # Kumpulkan SN dari borrow_detail_items
        serial_numbers = []
        for detail_item in detail.borrow_detail_items:
            if detail_item.inventory_item and detail_item.inventory_item.serial_number:
                serial_numbers.append(detail_item.inventory_item.serial_number)

        qty = detail.quantity or len(serial_numbers) or 1
        total_items += qty

        items_data.append({
            "loop_index": idx,
            "name": comp_name,
            "specs": specs,
            "serial_numbers": serial_numbers,
            "quantity": qty,
        })

    # Render Template Jinja2
    template = jinja_env.get_template("admin_borrow_alert.html")
    html_content = template.render(
        email_title=subject,
        badge_text=badge_text,
        badge_class=badge_class,
        headline=headline,
        admin_name=admin_user.full_name or admin_user.username,
        transaction_number=transaction.transaction_number or f"PJ-{transaction.id}",
        borrower_name=transaction.borrower.borrower_name if transaction.borrower else "-",
        borrower_institution=transaction.borrower.institution if (transaction.borrower and transaction.borrower.institution) else "-",
        borrower_phone=transaction.borrower.phone if (transaction.borrower and transaction.borrower.phone) else "-",
        borrower_email=transaction.borrower.email if (transaction.borrower and transaction.borrower.email) else None,
        borrow_date=format_date_id(transaction.borrow_date),
        expected_return_date=format_date_id(transaction.expected_return_date),
        status_days_desc=status_days_desc,
        officer_name=transaction.officer.officer_name if transaction.officer else "Petugas BMKG",
        purpose=transaction.purpose or transaction.item_description or "-",
        items=items_data,
        total_items=total_items,
        action_note=action_note,
        generated_at=datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    )


    return subject, html_content


async def send_single_transaction_alert(
    db: Session,
    transaction_id: int,
    notification_type: str = "manual",
    specific_admin_id: int | None = None,
) -> dict:
    """Mengirim alert/notifikasi untuk 1 transaksi peminjaman tertentu ke Admin (Hanya untuk status Dipinjam)."""
    transaction = db.query(BorrowTransaction).filter(BorrowTransaction.id == transaction_id).first()
    if not transaction:
        return {"success": False, "message": f"Transaksi peminjaman ID {transaction_id} tidak ditemukan."}

    if transaction.status not in ["Borrowed", "Dipinjam"]:
        return {
            "success": False,
            "message": f"Peringatan email hanya dapat dikirim untuk transaksi yang berstatus 'Dipinjam' (status saat ini: {transaction.status}).",
        }

    # Ambil penerima admin
    if specific_admin_id:
        admins = db.query(User).filter(User.id == specific_admin_id, User.is_active == True).all()
    else:
        admins = get_active_admin_users(db)

    if not admins:
        return {
            "success": False,
            "message": "Tidak ada akun Admin aktif yang memiliki alamat email di database.",
        }

    sent_count = 0
    errors = []

    for admin in admins:
        if not admin.email:
            continue

        subject, html_content = prepare_alert_email_content(transaction, notification_type, admin)
        success, err = await send_email_async(
            to_email=admin.email,
            subject=subject,
            html_content=html_content,
        )

        # Simpan ke tabel email_notification_logs
        log_entry = EmailNotificationLog(
            transaction_id=transaction.id,
            admin_user_id=admin.id,
            recipient_email=admin.email,
            notification_type=notification_type,
            subject=subject,
            status="success" if success else "failed",
            error_message=err,
        )
        db.add(log_entry)
        db.commit()

        if success:
            sent_count += 1
            # Catat juga ke Activity Log sistem
            ActivityLogService().log(
                db,
                user_id=admin.id,
                activity=f"Mengirim notifikasi email alert peminjaman {transaction.transaction_number or ''} ke {admin.email}",
                reference_table="borrow_transactions",
                reference_id=transaction.id,
                reference_path=f"/borrow/transactions/{transaction.id}",
                extra_data=f'{{"recipient": "{admin.email}", "type": "{notification_type}", "status": "success"}}',
            )
        else:
            errors.append(f"{admin.email}: {err}")
            ActivityLogService().log(
                db,
                user_id=admin.id,
                activity=f"Gagal mengirim notifikasi email alert peminjaman {transaction.transaction_number or ''} ke {admin.email}",
                reference_table="borrow_transactions",
                reference_id=transaction.id,
                reference_path=f"/borrow/transactions/{transaction.id}",
                extra_data=f'{{"recipient": "{admin.email}", "type": "{notification_type}", "error": "{err}"}}',
            )


    if sent_count > 0:
        return {
            "success": True,
            "message": f"Berhasil mengirim email alert ke {sent_count} admin.",
            "sent_count": sent_count,
            "errors": errors if errors else None,
        }
    else:
        return {
            "success": False,
            "message": f"Gagal mengirim email: {'; '.join(errors)}",
            "errors": errors,
        }


async def scan_and_send_due_reminders(db: Session, force: bool = False) -> dict:
    """Memindai seluruh peminjaman berstatus Dipinjam (Borrowed) dan mengirimkan alert ke Admin jika mendekati atau melewati jatuh tempo."""
    today = date.today()
    admins = get_active_admin_users(db)

    if not admins:
        logger.warning("Cron reminder: Tidak ada akun Admin dengan email terdaftar di database.")
        return {
            "success": False,
            "message": "Tidak ada akun Admin dengan email aktif untuk menerima notifikasi.",
            "processed_transactions": 0,
            "emails_sent": 0,
        }

    # Hanya ambil transaksi yang sedang aktif dipinjam (Borrowed / Dipinjam)
    active_transactions = (
        db.query(BorrowTransaction)
        .filter(
            BorrowTransaction.status.in_(["Borrowed", "Dipinjam"])
        )
        .all()
    )

    processed_count = 0
    sent_count = 0
    skipped_count = 0
    details = []

    for tx in active_transactions:
        days_diff = (tx.expected_return_date - today).days

        notif_type = None

        if days_diff == 2:
            notif_type = "h_minus_2"
        elif days_diff == 0:
            notif_type = "due_date"
        elif days_diff < 0:
            notif_type = "overdue"
        else:
            continue  # Belum masuk kategori pengingat (misal > 2 hari)

        processed_count += 1

        for admin in admins:
            if not admin.email:
                continue

            # Cek apakah sudah pernah terkirim ke admin ini untuk tipe yang sama hari ini (mencegah spam)
            if not force:
                already_sent = (
                    db.query(EmailNotificationLog)
                    .filter(
                        EmailNotificationLog.transaction_id == tx.id,
                        EmailNotificationLog.admin_user_id == admin.id,
                        EmailNotificationLog.notification_type == notif_type,
                        EmailNotificationLog.status == "success",
                        func.date(EmailNotificationLog.sent_at) == today,
                    )
                    .first()
                )
                if already_sent:
                    skipped_count += 1
                    continue

            # Kirim email
            subject, html_content = prepare_alert_email_content(tx, notif_type, admin)
            success, err = await send_email_async(
                to_email=admin.email,
                subject=subject,
                html_content=html_content,
            )

            # Catat log
            log_entry = EmailNotificationLog(
                transaction_id=tx.id,
                admin_user_id=admin.id,
                recipient_email=admin.email,
                notification_type=notif_type,
                subject=subject,
                status="success" if success else "failed",
                error_message=err,
            )
            db.add(log_entry)
            db.commit()

            if success:
                sent_count += 1
                details.append(f"Kirim ke {admin.email} untuk {tx.transaction_number} ({notif_type})")
            else:
                details.append(f"Gagal ke {admin.email}: {err}")

    # Catat pemindaian ke log aktivitas jika ada pemrosesan
    if sent_count > 0:
        ActivityLogService().log(
            db,
            user_id=None,
            activity=f"Pemindaian cron: Berhasil mengirim {sent_count} email alert peminjaman jatuh tempo ke Admin",
            reference_table="borrow_transactions",
            reference_id=None,
            reference_path="/borrow/transactions",
            extra_data=f'{{"emails_sent": {sent_count}, "processed_transactions": {processed_count}, "skipped": {skipped_count}}}',
        )

    logger.info(
        "Cron reminder selesai: %d transaksi diproses, %d email dikirim, %d diskip (sudah terkirim hari ini).",
        processed_count, sent_count, skipped_count,
    )

    return {
        "success": True,
        "processed_transactions": processed_count,
        "emails_sent": sent_count,
        "skipped_duplicates": skipped_count,
        "details": details,
    }


async def test_smtp_connection(to_email: str, db: Session | None = None, admin_user_id: int | None = None) -> dict:
    """Menguji koneksi SMTP dengan mengirim email uji coba ke alamat yang ditentukan."""
    template = jinja_env.get_template("test_smtp_email.html")
    now_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    html_content = template.render(
        sender_email=settings.SMTP_FROM_EMAIL or settings.SMTP_USER,
        recipient_email=to_email,
        smtp_host=settings.SMTP_HOST,
        smtp_port=settings.SMTP_PORT,
        test_time=now_str,
    )

    subject = "[TEST] Uji Coba Koneksi SMTP Sistem Inventaris BMKG"
    success, err = await send_email_async(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
    )

    if db:
        log_entry = EmailNotificationLog(
            transaction_id=None,
            admin_user_id=admin_user_id,
            recipient_email=to_email,
            notification_type="test",
            subject=subject,
            status="success" if success else "failed",
            error_message=err,
        )
        db.add(log_entry)
        db.commit()

        # Catat ke Activity Log sistem
        ActivityLogService().log(
            db,
            user_id=admin_user_id,
            activity=f"Uji coba koneksi SMTP email ke {to_email} ({'Berhasil' if success else 'Gagal'})",
            reference_table="email_notification_logs",
            reference_id=log_entry.id,
            reference_path="/borrow/transactions",
            extra_data=f'{{"recipient": "{to_email}", "status": "{"success" if success else "failed"}"}}',
        )

    return {
        "success": success,
        "message": "Email uji coba berhasil dikirim! Silakan periksa inbox/spam email Anda." if success else f"Gagal mengirim email uji coba: {err}",
        "recipient": to_email,
        "error": err,
    }

