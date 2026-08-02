"""Borrow extensions endpoints — perpanjangan peminjaman."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user, get_current_user
from app.models.user import User
from app.schemas.borrow_extension import BorrowExtensionCreate
from app.services.borrow_extension_service import BorrowExtensionService

router = APIRouter(prefix="/api/v1/borrow/transactions", tags=["Borrow Extensions"])


@router.get("/{borrow_id}/extensions")
def list_extensions(
    borrow_id: int,
    db: Session = Depends(get_db),
):
    """Daftar riwayat perpanjangan untuk satu transaksi — public read."""
    service = BorrowExtensionService()
    exts = service.get_extensions_by_borrow(db, borrow_id)
    return {
        "status": "success", "message": "Daftar perpanjangan berhasil diambil",
        "data": [e.model_dump() for e in exts],
    }


@router.post("/{borrow_id}/extensions", status_code=201)
def request_extension(
    borrow_id: int,
    data: BorrowExtensionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ajukan perpanjangan peminjaman — user/admin login."""
    service = BorrowExtensionService()
    ext = service.request_extension(db, borrow_id, data, current_user)
    return {"status": "success", "message": "Perpanjangan berhasil diajukan", "data": ext.model_dump()}


@router.put("/{borrow_id}/extensions/{extension_id}/approve")
def approve_extension(
    borrow_id: int,
    extension_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Setujui perpanjangan — Admin only."""
    service = BorrowExtensionService()
    ext = service.approve_extension(db, borrow_id, extension_id, current_user)
    return {"status": "success", "message": "Perpanjangan disetujui", "data": ext.model_dump()}


@router.put("/{borrow_id}/extensions/{extension_id}/reject")
def reject_extension(
    borrow_id: int,
    extension_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Tolak perpanjangan — Admin only."""
    service = BorrowExtensionService()
    ext = service.reject_extension(db, borrow_id, extension_id, current_user)
    return {"status": "success", "message": "Perpanjangan ditolak", "data": ext.model_dump()}
