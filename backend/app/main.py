from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
import traceback

from app.api.v1.endpoints.activity_logs import router as activity_logs_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.borrow import router as borrow_router
from app.api.v1.endpoints.borrow_extensions import router as borrow_extensions_router
from app.api.v1.endpoints.borrowers import router as borrowers_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.handovers import router as handovers_router
from app.api.v1.endpoints.inventory import router as inventory_router
from app.api.v1.endpoints.inventory_statuses import router as statuses_router
from app.api.v1.endpoints.maintenance import router as maintenance_router
from app.api.v1.endpoints.officers import router as officers_router
from app.api.v1.endpoints.reminders import router as reminders_router
from app.api.v1.endpoints.returns import router as returns_router
from app.api.v1.endpoints.uploads import router as uploads_router
from app.api.v1.endpoints.upts import router as upts_router
from app.api.v1.endpoints.users import router as users_router
from app.core.config import settings
from app.core.database import engine
from app.core.logging_config import setup_logging, get_logger
from app.core.scheduler import start_scheduler, stop_scheduler

# Siapkan logging file server di awal startup
setup_logging()
logger = get_logger()

app = FastAPI(
    title="Sistem Inventaris Alat BMKG",
    description="REST API untuk mengelola inventaris alat BMKG",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(borrowers_router)
app.include_router(statuses_router)
app.include_router(handovers_router)
app.include_router(upts_router)
app.include_router(inventory_router)
app.include_router(borrow_router)
app.include_router(borrow_extensions_router)
app.include_router(returns_router)
app.include_router(maintenance_router)
app.include_router(officers_router)
app.include_router(reminders_router)
app.include_router(activity_logs_router)
app.include_router(dashboard_router)
app.include_router(uploads_router)

# Mount folder uploads sebagai static files (akses via /uploads/<path>)
import os
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    """Tangkap error tak terduga (500) dan catat ke file log server
    dengan traceback lengkap (termasuk nama fungsi & baris kode)."""
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.error("Unhandled exception on %s %s:\n%s", request.method, request.url.path, tb)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Terjadi kesalahan pada server. Silakan coba lagi."},
    )


@app.get("/health")
def health_check():
    """Health check endpoint — verifikasi server dan database berjalan."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception:
        return {"status": "ok", "database": "disconnected"}


@app.on_event("startup")
async def startup_event():
    """Test koneksi database dan jalankan background task scheduler saat server mulai."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[OK] Database connection successful")
    except Exception as e:
        print(f"[WARN] Database connection failed: {e}")

    # Jalankan background scheduler untuk pengingat otomatis harian
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    """Hentikan background task scheduler saat server dimatikan."""
    stop_scheduler()