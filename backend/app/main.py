from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

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
from app.api.v1.endpoints.returns import router as returns_router
from app.api.v1.endpoints.uploads import router as uploads_router
from app.api.v1.endpoints.users import router as users_router
from app.core.config import settings
from app.core.database import engine

app = FastAPI(
    title="Sistem Inventaris Alat Sensor BMKG",
    description="REST API untuk mengelola inventaris alat sensor BMKG",
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
app.include_router(inventory_router)
app.include_router(borrow_router)
app.include_router(borrow_extensions_router)
app.include_router(returns_router)
app.include_router(maintenance_router)
app.include_router(officers_router)
app.include_router(activity_logs_router)
app.include_router(dashboard_router)
app.include_router(uploads_router)

# Mount folder uploads sebagai static files (akses via /uploads/<path>)
import os
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


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
    """Test koneksi database saat server mulai."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[OK] Database connection successful")
    except Exception as e:
        print(f"[WARN] Database connection failed: {e}")