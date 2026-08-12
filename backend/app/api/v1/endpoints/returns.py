"""Returns endpoints — pengembalian inventaris. (FR-23 s.d FR-27, UR-07)"""
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_admin_user, get_current_user
from app.core.upload import delete_upload
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
    current_user: User = Depends(get_current_user),
):
    """Upload dokumen pengembalian yang sudah ditandatangani. Wajib login. Hanya untuk status Menunggu Verifikasi."""
    # Validasi ekstensi
    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
    ext = os.path.splitext(file.filename or "document.pdf")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Format file tidak didukung: {ext}. Gunakan PDF, PNG, atau JPG.")

    # Validasi ukuran (max 10 MB)
    contents = file.file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Ukuran file maksimal 10 MB.")

    # Ambil data pengembalian untuk cek status SEBELUM menulis file
    service = ReturnService()
    ret = service.get_return_detail(db, return_id)
    if ret.status != "Menunggu Verifikasi":
        raise HTTPException(status_code=400, detail=f"Upload dokumen hanya bisa dilakukan saat status Menunggu Verifikasi. Status saat ini: {ret.status}.")

    # Hapus file lama jika ada
    if ret.signed_document:
        delete_upload(ret.signed_document)

    # Simpan file ke folder uploads
    upload_dir = os.path.join(settings.UPLOAD_DIR, "documents")
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(upload_dir, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    # Simpan path relatif ke database
    doc_path = f"documents/{filename}"
    service = ReturnService()
    ret = service.upload_signed_document(db, return_id, doc_path, current_user)
    return {"status": "success", "message": "Dokumen tertandatangan berhasil diupload", "data": ret.model_dump()}


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


@router.put("/{return_id}/reject")
def reject_return(
    return_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Admin menolak pengembalian — batalkan return, peminjaman tetap Dipinjam."""
    service = ReturnService()
    ret = service.reject_return(db, return_id, current_user)
    return {"status": "success", "message": "Pengembalian ditolak", "data": ret.model_dump()}


# ═══════════ DELETE ═══════════

@router.delete("/{return_id}")
def delete_return(
    return_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Hapus pengembalian — Admin only. Hanya status 'Menunggu Verifikasi'."""
    service = ReturnService()
    result = service.delete_return(db, return_id, current_user)
    return result
