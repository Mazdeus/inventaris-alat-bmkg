"""Maintenance endpoints — riwayat pemeliharaan komponen. (UR-08, FR-26)"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate
from app.services.maintenance_service import MaintenanceService
from app.services.transaction_snapshot_service import TransactionSnapshotService

router = APIRouter(prefix="/api/v1/maintenance", tags=["Pemeliharaan"])


@router.get("")
def list_maintenance(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    component_id: int | None = Query(None, description="Filter ID komponen"),
    status: str | None = Query(None, description="Filter status"),
    db: Session = Depends(get_db),
):
    service = MaintenanceService()
    items, total = service.get_maintenances(db, page=page, size=size, component_id=component_id, status=status)
    return {
        "status": "success", "message": "Daftar pemeliharaan berhasil diambil",
        "data": [m.model_dump() for m in items],
        "meta": {"page": page, "size": size, "total": total, "total_pages": max(1, (total + size - 1) // size)},
    }


@router.post("", status_code=201)
def create_maintenance(
    data: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Catat pemeliharaan baru — status item otomatis jadi Maintenance. Admin only."""
    service = MaintenanceService()
    m = service.create_maintenance(db, data, current_user)
    return {"status": "success", "message": "Data pemeliharaan berhasil dicatat", "data": m.model_dump()}


@router.get("/{maintenance_id}")
def get_maintenance(
    maintenance_id: int,
    db: Session = Depends(get_db),
):
    service = MaintenanceService()
    m = service.get_maintenance_detail(db, maintenance_id)
    return {"status": "success", "message": "Data pemeliharaan ditemukan", "data": m.model_dump()}


@router.get("/{maintenance_id}/snapshot")
def get_maintenance_snapshot(
    maintenance_id: int,
    db: Session = Depends(get_db),
):
    """Snapshot arsip pemeliharaan saat selesai/dibatalkan — public read."""
    snapshot_svc = TransactionSnapshotService()
    snap = snapshot_svc.get_snapshot(db, transaction_type="maintenance", transaction_id=maintenance_id)
    return {"status": "success", "message": "Snapshot pemeliharaan ditemukan", "data": snap}


@router.put("/{maintenance_id}")
def update_maintenance(
    maintenance_id: int,
    data: MaintenanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Update pemeliharaan — jika Completed + end_date → status item jadi Available."""
    service = MaintenanceService()
    m = service.update_maintenance(db, maintenance_id, data, current_user)
    return {"status": "success", "message": "Data pemeliharaan berhasil diperbarui", "data": m.model_dump()}
