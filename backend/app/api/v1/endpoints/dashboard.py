"""Dashboard endpoint — statistik & grafik. (FR-30, FR-31, UR-11)"""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_summary(
    db: Session = Depends(get_db),
):
    """Ringkasan statistik inventaris — public."""
    service = DashboardService()
    return {"status": "success", "message": "Data dashboard berhasil diambil", "data": service.get_summary(db)}


@router.get("/charts")
def get_charts(
    year: int | None = Query(None, description="Tahun data (default: tahun ini)"),
    db: Session = Depends(get_db),
):
    """Data grafik — tren peminjaman per bulan, distribusi status, pengadaan per tahun — public."""
    service = DashboardService()
    return {"status": "success", "message": "Data grafik berhasil diambil", "data": service.get_charts(db, year or date.today().year)}
