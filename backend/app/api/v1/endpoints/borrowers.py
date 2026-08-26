"""Borrowers endpoints — CRUD data peminjam. (UR-21, FR-16)"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.schemas.borrower import BorrowerCreate, BorrowerUpdate
from app.services.borrower_service import BorrowerService

router = APIRouter(prefix="/api/v1/borrowers", tags=["Borrowers"])


@router.get("")
def list_borrowers(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    borrower_type: str | None = Query(None, description="Filter: Internal / External"),
    search: str | None = Query(None, description="Cari nama peminjam"),
    db: Session = Depends(get_db),
):
    """Daftar peminjam — public read."""
    service = BorrowerService()
    borrowers, total = service.get_borrowers(db, page=page, size=size, borrower_type=borrower_type, search=search)
    return {
        "status": "success",
        "message": "Daftar peminjam berhasil diambil",
        "data": [b.model_dump() for b in borrowers],
        "meta": {"page": page, "size": size, "total": total, "total_pages": max(1, (total + size - 1) // size)},
    }


@router.post("", status_code=201)
def create_borrower(
    data: BorrowerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Tambah peminjam baru — hanya Admin. (UR-21)"""
    service = BorrowerService()
    borrower = service.create_borrower(db, data, current_user)
    return {"status": "success", "message": "Data peminjam berhasil ditambahkan", "data": borrower.model_dump()}


@router.get("/{borrower_id}")
def get_borrower(
    borrower_id: int,
    db: Session = Depends(get_db),
):
    """Detail peminjam — public read."""
    service = BorrowerService()
    borrower = service.get_borrower(db, borrower_id)
    return {"status": "success", "message": "Data peminjam ditemukan", "data": borrower.model_dump()}


@router.put("/{borrower_id}")
def update_borrower(
    borrower_id: int,
    data: BorrowerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Update peminjam — hanya Admin."""
    service = BorrowerService()
    borrower = service.update_borrower(db, borrower_id, data)
    return {"status": "success", "message": "Data peminjam berhasil diperbarui", "data": borrower.model_dump()}


class BulkDeleteRequest(BaseModel):
    ids: list[int] = Field(..., min_length=1, description="Daftar ID peminjam yang akan dihapus")


@router.delete("/bulk")
def bulk_delete_borrowers(
    data: BulkDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Hapus banyak peminjam sekaligus — hanya Admin."""
    service = BorrowerService()
    result = service.bulk_delete_borrowers(db, data.ids)
    return {
        "status": "success",
        "message": f"Berhasil menghapus {result['deleted']} peminjam",
        "data": result,
    }
