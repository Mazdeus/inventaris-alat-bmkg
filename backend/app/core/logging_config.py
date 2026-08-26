"""Konfigurasi logging file server (Python logging).

Log ditulis ke file (rotasi harian, retensi 30 hari) dan ditampilkan ke konsol.
Digunakan untuk melacak error dan operasi penting di service layer.
"""
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

LOGGER_NAME = "inventaris_bmkg"

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "app.log"

_LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] %(message)s"


def setup_logging() -> logging.Logger:
    """Siapkan logger global. Dipanggil sekali saat aplikasi startup."""
    logger = logging.getLogger(LOGGER_NAME)

    # Hindari duplicate handler saat reload (uvicorn --reload)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(_LOG_FORMAT)

    # Handler file: rotasi harian (midnight), simpan 30 file terakhir
    os.makedirs(LOG_DIR, exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        LOG_FILE,
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # Handler konsol
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    return logger


def get_logger() -> logging.Logger:
    """Ambil logger global. Jika belum di-setup, setup dulu (fallback)."""
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        setup_logging()
    return logger
