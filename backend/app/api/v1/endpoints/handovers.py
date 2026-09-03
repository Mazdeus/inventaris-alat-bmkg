from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.core.documents import generate_handover_document
from app.core.upload import delete_upload
from app.models.handover import Handover
from app.models.user import User
from app.schemas.handover import HandoverCreate, HandoverUpdate
from app.services.handover_service import HandoverService
from app.services.transaction_snapshot_service import TransactionSnapshotService


router = APIRouter(prefix="/api/v1/handovers", tags=["Handovers"])


@router.get("")
def list_handovers(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: str | None = Query(None, description="Cari UPT penerima"),
    status: str | None = Query(None, description="Draft / Transferred / Cancelled"),
    db: Session = Depends(get_db),
):
    """Daftar transaksi pelimpahan — public read."""
    service = HandoverService()
    handovers, total = service.get_handovers(db, page=page, size=size, search=search, status=status)
    return {
        "status": "success", "message": "Daftar pelimpahan berhasil diambil",
        "data": [h.model_dump() for h in handovers],
        "meta": {"page": page, "size": size, "total": total, "total_pages": max(1, (total + size - 1) // size)},
    }


@router.post("", status_code=201)
def create_handover(
    data: HandoverCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Buat pelimpahan baru — Admin only. Status awal: Draft."""
    service = HandoverService()
    h = service.create_handover(db, data, current_user)
    return {"status": "success", "message": "Pelimpahan berhasil dibuat", "data": h.model_dump()}


@router.get("/{handover_id}")
def get_handover(
    handover_id: int,
    db: Session = Depends(get_db),
):
    """Detail transaksi pelimpahan — public read."""
    service = HandoverService()
    h = service.get_handover_detail(db, handover_id)
    return {"status": "success", "message": "Data pelimpahan ditemukan", "data": h.model_dump()}


@router.get("/{handover_id}/snapshot")
def get_handover_snapshot(
    handover_id: int,
    db: Session = Depends(get_db),
):
    """Snapshot arsip transaksi pelimpahan saat selesai/dibatalkan — public read."""
    snapshot_svc = TransactionSnapshotService()
    snap = snapshot_svc.get_snapshot(db, transaction_type="handover", transaction_id=handover_id)
    return {"status": "success", "message": "Snapshot pelimpahan ditemukan", "data": snap}


@router.put("/{handover_id}/complete")
def complete_handover(
    handover_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Selesaikan pelimpahan — Admin only. Draft → Transferred."""
    service = HandoverService()
    h = service.complete_handover(db, handover_id, current_user)
    return {"status": "success", "message": "Pelimpahan berhasil diselesaikan", "data": h.model_dump()}


@router.put("/{handover_id}/cancel")
def cancel_handover(
    handover_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Batalkan pelimpahan — Admin only. Draft → Cancelled."""
    service = HandoverService()
    h = service.cancel_handover(db, handover_id, current_user)
    return {"status": "success", "message": "Pelimpahan dibatalkan", "data": h.model_dump()}


# ═══════════ DOKUMEN ═══════════

@router.get("/{handover_id}/document")
def download_document(
    handover_id: int,
    db: Session = Depends(get_db),
):
    """Download dokumen BAST PDF pelimpahan — public."""
    h = db.query(Handover).filter(Handover.id == handover_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Data pelimpahan tidak ditemukan")

    pdf_bytes = generate_handover_document(h)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=BAST_Pelimpahan_{handover_id}.pdf"},
    )



@router.post("/{handover_id}/document")
def upload_signed_document(
    handover_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload dokumen pelimpahan — publik (tanpa login). Hanya saat status Draft."""
    import os
    import uuid

    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
    ext = os.path.splitext(file.filename or "document.pdf")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Format file tidak didukung: {ext}. Gunakan PDF, PNG, atau JPG.")

    contents = file.file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Ukuran file maksimal 10 MB.")

    service = HandoverService()
    h = service.get_handover_detail(db, handover_id)
    if h.status != "Draft":
        raise HTTPException(status_code=400, detail=f"Upload dokumen hanya bisa saat status Draft. Status saat ini: {h.status}.")

    if h.signed_document:
        delete_upload(h.signed_document)

    upload_dir = os.path.join(settings.UPLOAD_DIR, "documents")
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(upload_dir, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    doc_path = f"documents/{filename}"
    # Upload tanpa user login — gunakan system user
    h_doc = service.upload_signed_document_public(db, handover_id, doc_path)
    return {"status": "success", "message": "Dokumen pelimpahan berhasil diupload", "data": h_doc.model_dump()}


# ═══════════ UPDATE ═══════════

@router.put("/{handover_id}")
def update_handover(
    handover_id: int,
    data: HandoverUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Update pelimpahan — Admin only. Hanya status Draft."""
    service = HandoverService()
    h = service.update_handover(db, handover_id, data, current_user)
    return {"status": "success", "message": "Pelimpahan berhasil diperbarui", "data": h.model_dump()}


# ═══════════ DELETE ═══════════

@router.delete("/{handover_id}")
def delete_handover(
    handover_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Hapus pelimpahan — Admin only. Hanya status Draft."""
    service = HandoverService()
    result = service.delete_handover(db, handover_id, current_user)
    return result
