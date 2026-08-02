"""Inventory Statuses endpoint — lookup daftar status komponen. (FR-14)"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.inventory_status import InventoryStatus

router = APIRouter(prefix="/api/v1/inventory/statuses", tags=["Inventory"])


@router.get("")
def list_statuses(
    db: Session = Depends(get_db),
):
    """Daftar semua status komponen inventaris — untuk dropdown/filter."""
    statuses = db.query(InventoryStatus).all()
    return {
        "status": "success",
        "message": "Daftar status berhasil diambil",
        "data": [{"id": s.id, "status_name": s.status_name} for s in statuses],
    }
