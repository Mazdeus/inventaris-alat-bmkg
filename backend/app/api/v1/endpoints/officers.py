"""Officers endpoints — CRUD data petugas. (UR-22)"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.schemas.officer import OfficerCreate, OfficerUpdate
from app.services.officer_service import OfficerService

router = APIRouter(prefix="/api/v1/officers", tags=["Officers"])


@router.get("")
def list_officers(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: str | None = Query(None, description="Cari nama petugas"),
    is_active: bool | None = Query(None, description="Filter status aktif"),
    db: Session = Depends(get_db),
):
    """Daftar petugas — public read."""
    service = OfficerService()
    officers, total = service.get_officers(db, page=page, size=size, search=search, is_active=is_active)
    return {
        "status": "success",
        "message": "Daftar petugas berhasil diambil",
        "data": [o.model_dump() for o in officers],
        "meta": {"page": page, "size": size, "total": total, "total_pages": max(1, (total + size - 1) // size)},
    }


@router.post("", status_code=201)
def create_officer(
    data: OfficerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Tambah petugas baru — hanya Admin."""
    service = OfficerService()
    officer = service.create_officer(db, data, current_user)
    return {"status": "success", "message": "Data petugas berhasil ditambahkan", "data": officer.model_dump()}


@router.get("/{officer_id}")
def get_officer(
    officer_id: int,
    db: Session = Depends(get_db),
):
    """Detail petugas — public read."""
    service = OfficerService()
    officer = service.get_officer(db, officer_id)
    return {"status": "success", "message": "Data petugas ditemukan", "data": officer.model_dump()}


@router.put("/{officer_id}")
def update_officer(
    officer_id: int,
    data: OfficerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Update petugas — hanya Admin."""
    service = OfficerService()
    officer = service.update_officer(db, officer_id, data)
    return {"status": "success", "message": "Data petugas berhasil diperbarui", "data": officer.model_dump()}


@router.delete("/{officer_id}")
def delete_officer(
    officer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Hapus petugas — hanya Admin. Petugas yang terkait transaksi tidak bisa dihapus."""
    service = OfficerService()
    result = service.delete_officer(db, officer_id)
    return result
