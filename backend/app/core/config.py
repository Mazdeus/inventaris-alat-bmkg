from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DEBUG: bool = True
    UPLOAD_DIR: str = str(Path(__file__).resolve().parent.parent.parent / "uploads")
    BASE_URL: str = "http://localhost:8000"

    # Konfigurasi SMTP Email
    SMTP_ENABLED: bool = True
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "Sistem Inventaris BMKG"
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False

    # Jadwal Cron Penjadwal Peringatan (Jam & Menit)
    EMAIL_REMINDER_CRON_HOUR: int = 8
    EMAIL_REMINDER_CRON_MINUTE: int = 0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
