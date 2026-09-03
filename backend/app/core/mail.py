"""Modul pengiriman email asinkron menggunakan aiosmtplib (100% Gratis via Gmail SMTP)."""
from email.message import EmailMessage
from email.utils import formataddr
import aiosmtplib
import traceback

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger()


async def send_email_async(
    to_email: str,
    subject: str,
    html_content: str,
    plain_text_content: str | None = None,
) -> tuple[bool, str | None]:
    """Mengirim email HTML secara asinkron via SMTP (misal Gmail App Password).

    Args:
        to_email: Alamat email penerima.
        subject: Subjek email.
        html_content: Isi pesan dalam format HTML.
        plain_text_content: Alternatif teks biasa (fallback).

    Returns:
        tuple (success: bool, error_message: str | None)
    """
    if not settings.SMTP_ENABLED:
        logger.warning("Email tidak dikirim karena SMTP_ENABLED=False di konfigurasi server.")
        return False, "Layanan SMTP dinonaktifkan di konfigurasi server (SMTP_ENABLED=false)."

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        msg = "Kredensial SMTP belum lengkap (SMTP_USER atau SMTP_PASSWORD kosong di .env)."
        logger.warning(msg)
        return False, msg

    try:
        # Siapkan struktur MIME Email
        message = EmailMessage()
        sender_name = settings.SMTP_FROM_NAME or "Sistem Inventaris BMKG"
        from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
        
        message["From"] = formataddr((sender_name, from_email))
        message["To"] = to_email
        message["Subject"] = subject

        # Plaintext fallback jika client email tidak render HTML
        fallback_text = plain_text_content or "Silakan buka email ini di aplikasi yang mendukung format HTML."
        message.set_content(fallback_text)
        message.add_alternative(html_content, subtype="html")

        # Bersihkan spasi jika ada (Google sering menampilkan dengan spasi per 4 huruf)
        clean_password = settings.SMTP_PASSWORD.replace(" ", "").strip()

        # Kirim asinkron via aiosmtplib
        # Port 587 menggunakan STARTTLS, Port 465 menggunakan SSL langsung
        use_tls = settings.SMTP_TLS if settings.SMTP_PORT != 465 else False
        use_ssl = settings.SMTP_SSL if settings.SMTP_PORT == 465 else False

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER.strip(),
            password=clean_password,
            start_tls=use_tls,
            use_tls=use_ssl,
            timeout=25,
        )


        logger.info("Email berhasil terkirim ke: %s (Subjek: '%s')", to_email, subject)
        return True, None

    except aiosmtplib.SMTPAuthenticationError as e:
        err = f"Autentikasi SMTP Gagal (cek username & Google App Password): {e}"
        logger.error("SMTP Authentication Error saat mengirim ke %s: %s", to_email, err)
        return False, err
    except aiosmtplib.SMTPConnectError as e:
        err = f"Gagal terhubung ke server SMTP ({settings.SMTP_HOST}:{settings.SMTP_PORT}): {e}"
        logger.error("SMTP Connection Error saat mengirim ke %s: %s", to_email, err)
        return False, err
    except Exception as e:
        err = f"Terjadi kesalahan saat pengiriman email: {str(e)}"
        logger.error("Error tidak terduga saat kirim email ke %s:\n%s", to_email, traceback.format_exc())
        return False, err
