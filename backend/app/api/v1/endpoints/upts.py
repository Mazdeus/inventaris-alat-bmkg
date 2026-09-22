"""UPT endpoints — CRUD data Unit Pelaksana Teknis (UPT) BMKG."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.schemas.upt import UptCreate, UptUpdate
from app.services.upt_service import UptService

router = APIRouter(prefix="/api/v1/upts", tags=["UPT"])


@router.get("")
def list_upts(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=10000),
    search: str | None = Query(None, description="Cari nama atau alamat UPT"),
    is_active: bool | None = Query(None, description="Filter status aktif"),
    order_dir: str = Query("asc", description="Urutan asc atau desc"),
    db: Session = Depends(get_db),
):
    """Daftar UPT — public read."""
    service = UptService()
    upts, total = service.get_upts(
        db, page=page, size=size, search=search, is_active=is_active, order_dir=order_dir
    )
    return {
        "status": "success",
        "message": "Daftar UPT berhasil diambil",
        "data": [u.model_dump() for u in upts],
        "meta": {"page": page, "size": size, "total": total, "total_pages": max(1, (total + size - 1) // size)},
    }


@router.post("", status_code=201)
def create_upt(
    data: UptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Tambah UPT baru — hanya Admin."""
    service = UptService()
    upt = service.create_upt(db, data, current_user)
    return {"status": "success", "message": "Data UPT berhasil ditambahkan", "data": upt.model_dump()}


@router.get("/{upt_id}")
def get_upt(
    upt_id: int,
    db: Session = Depends(get_db),
):
    """Detail UPT — public read."""
    service = UptService()
    upt = service.get_upt(db, upt_id)
    return {"status": "success", "message": "Data UPT ditemukan", "data": upt.model_dump()}


@router.put("/{upt_id}")
def update_upt(
    upt_id: int,
    data: UptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Update UPT — hanya Admin."""
    service = UptService()
    upt = service.update_upt(db, upt_id, data, current_user)
    return {"status": "success", "message": "Data UPT berhasil diperbarui", "data": upt.model_dump()}


@router.delete("/{upt_id}")
def delete_upt(
    upt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Hapus UPT — hanya Admin (soft delete)."""
    service = UptService()
    result = service.delete_upt(db, upt_id, current_user)
    return result
