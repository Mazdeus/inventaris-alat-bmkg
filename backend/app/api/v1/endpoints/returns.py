"""Returns endpoints — pengembalian inventaris. (FR-23 s.d FR-27, UR-07)"""
import os
import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user, get_current_user_optional
from app.models.user import User
from app.schemas.return_ import ReturnCreate
from app.services.return_service import ReturnService

router = APIRouter(prefix="/api/v1/returns", tags=["Returns"])


@router.get("")
def list_returns(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    start_date: str | None = Query(None, description="Filter tanggal awal"),
    end_date: str | None = Query(None, description="Filter tanggal akhir"),
    db: Session = Depends(get_db),
):
    service = ReturnService()
    from datetime import date as dt_date
    sd = dt_date.fromisoformat(start_date) if start_date else None
    ed = dt_date.fromisoformat(end_date) if end_date else None
    rets, total = service.get_returns(db, page=page, size=size, start_date=sd, end_date=ed)
    return {
        "status": "success", "message": "Daftar pengembalian berhasil diambil",
        "data": [r.model_dump() for r in rets],
        "meta": {"page": page, "size": size, "total": total, "total_pages": max(1, (total + size - 1) // size)},
    }


@router.post("", status_code=201)
def create_return(
    data: ReturnCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Proses pengembalian — update status per SN, status komponen otomatis. Admin only."""
    service = ReturnService()
    ret = service.create_return(db, data, current_user)
    return {"status": "success", "message": "Pengembalian berhasil diproses", "data": ret.model_dump()}


@router.get("/{return_id}")
def get_return(
    return_id: int,
    db: Session = Depends(get_db),
):
    service = ReturnService()
    ret = service.get_return_detail(db, return_id)
    return {"status": "success", "message": "Data pengembalian ditemukan", "data": ret.model_dump()}


# ═══════════ DOKUMEN TANDA TANGAN ═══════════

@router.get("/{return_id}/document")
def download_document(
    return_id: int,
    db: Session = Depends(get_db),
):
    """Download template dokumen pengembalian — public (tanpa login)."""
    service = ReturnService()
    return service.download_document(db, return_id)


@router.post("/{return_id}/document")
def upload_signed_document(
    return_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Upload dokumen pengembalian yang sudah ditandatangani — public (tanpa login) atau authenticated."""
    # Simpan file ke folder uploads
    upload_dir = os.path.join("uploads", "documents")
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(file.filename or "document.pdf")[1] or ".pdf"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(upload_dir, filename)

    contents = file.file.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    # Simpan path relatif ke database
    doc_path = f"documents/{filename}"
    service = ReturnService()
    user = current_user if current_user else None
    tx = service.upload_signed_document(db, return_id, doc_path, user)
    return {"status": "success", "message": "Dokumen tertandatangan berhasil diupload", "data": tx.model_dump()}


# ═══════════ VERIFIKASI ═══════════

@router.put("/{return_id}/verify")
def verify_return(
    return_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Admin memverifikasi pengembalian — ubah status menjadi Selesai."""
    service = ReturnService()
    ret = service.verify_return(db, return_id, current_user)
    return {"status": "success", "message": "Pengembalian berhasil diverifikasi", "data": ret.model_dump()}
