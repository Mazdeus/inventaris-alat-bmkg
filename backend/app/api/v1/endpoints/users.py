"""Users endpoints — CRUD pengguna (Admin only). (UR-01)"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("")
def list_users(
    page: int = Query(1, ge=1, description="Halaman"),
    size: int = Query(10, ge=1, le=100, description="Jumlah per halaman"),
    is_active: bool | None = Query(None, description="Filter status aktif"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Daftar seluruh pengguna — hanya Admin."""
    service = UserService()
    users, total = service.get_users(db, page=page, size=size, is_active=is_active)
    return {
        "status": "success",
        "message": "Daftar user berhasil diambil",
        "data": users,
        "meta": {
            "page": page,
            "size": size,
            "total": total,
            "total_pages": max(1, (total + size - 1) // size),
        },
    }


@router.post("", status_code=201)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Tambah pengguna baru — hanya Admin. (UR-01)"""
    service = UserService()
    user = service.create_user(db, data)
    return {"status": "success", "message": "User berhasil dibuat", "data": user.model_dump()}


@router.get("/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Detail pengguna — hanya Admin."""
    service = UserService()
    user = service.get_user(db, user_id)
    return {"status": "success", "message": "Data user ditemukan", "data": user.model_dump()}


@router.put("/{user_id}")
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Update pengguna — hanya Admin. Semua field opsional (partial update)."""
    service = UserService()
    user = service.update_user(db, user_id, data)
    return {"status": "success", "message": "User berhasil diperbarui", "data": user.model_dump()}


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Hapus pengguna — hanya Admin. Jika user punya riwayat transaksi → soft delete."""
    service = UserService()
    result = service.delete_user(db, user_id)
    return result
