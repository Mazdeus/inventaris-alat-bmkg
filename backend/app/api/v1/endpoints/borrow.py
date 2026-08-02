"""Borrow endpoints — transaksi peminjaman inventaris. (FR-15 s.d FR-22, FR-27, FR-35)"""
from io import BytesIO

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user, get_current_user, get_current_user_optional
from app.models.user import User
from app.schemas.borrow import ApprovalUpdate, BorrowTransactionCreate, BulkDeleteRequest
from app.services.borrow_service import BorrowService

router = APIRouter(prefix="/api/v1/borrow/transactions", tags=["Borrow Transactions"])


@router.get("")
def list_transactions(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    start_date: str | None = Query(None, description="Filter tanggal awal (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="Filter tanggal akhir (YYYY-MM-DD)"),
    borrower_name: str | None = Query(None, description="Cari nama peminjam"),
    status: str | None = Query(None, description="Menunggu / Dipinjam / Dikembalikan / Dibatalkan"),
    db: Session = Depends(get_db),
):
    """Daftar transaksi peminjaman — public read."""
    service = BorrowService()
    from datetime import date as dt_date
    sd = dt_date.fromisoformat(start_date) if start_date else None
    ed = dt_date.fromisoformat(end_date) if end_date else None
    txs, total = service.get_transactions(
        db, current_user=None, page=page, size=size,
        start_date=sd, end_date=ed, borrower_name=borrower_name,
        status=status,
    )
    return {
        "status": "success", "message": "Daftar transaksi berhasil diambil",
        "data": [tx.model_dump() for tx in txs],
        "meta": {"page": page, "size": size, "total": total, "total_pages": max(1, (total + size - 1) // size)},
    }


@router.post("", status_code=201)
def create_transaction(
    data: BorrowTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Buat transaksi peminjaman baru + validasi stok. Status awal: Menunggu."""
    service = BorrowService()
    tx = service.create_borrow(db, data, current_user)
    return {"status": "success", "message": "Transaksi peminjaman berhasil dibuat", "data": tx.model_dump()}


@router.get("/{transaction_id}")
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    """Detail transaksi peminjaman beserta rincian komponen — public read."""
    service = BorrowService()
    tx = service.get_transaction_detail(db, transaction_id)
    return {"status": "success", "message": "Data transaksi ditemukan", "data": tx.model_dump()}


@router.put("/{transaction_id}/approve")
def approve_transaction(
    transaction_id: int,
    data: ApprovalUpdate | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Approve peminjaman — Admin only. Status Menunggu → Dipinjam."""
    service = BorrowService()
    tx = service.approve_borrow(db, transaction_id, current_user)
    return {"status": "success", "message": "Transaksi peminjaman berhasil disetujui", "data": tx.model_dump()}


@router.put("/{transaction_id}/reject")
def reject_transaction(
    transaction_id: int,
    data: ApprovalUpdate | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Tolak peminjaman — Admin only. Status Menunggu → Dibatalkan."""
    service = BorrowService()
    reason = data.reason if data else None
    tx = service.reject_borrow(db, transaction_id, reason, current_user)
    return {"status": "success", "message": "Transaksi peminjaman ditolak", "data": tx.model_dump()}


@router.put("/{transaction_id}/cancel")
def cancel_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Batalkan transaksi peminjaman — Admin only. Status Dipinjam → Dibatalkan."""
    service = BorrowService()
    tx = service.cancel_borrow(db, transaction_id, current_user)
    return {"status": "success", "message": "Transaksi peminjaman dibatalkan", "data": tx.model_dump()}


@router.delete("/bulk")
def bulk_delete_transactions(
    data: BulkDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Hapus transaksi peminjaman secara massal — Admin only. Hanya Dikembalikan & Dibatalkan."""
    service = BorrowService()
    result = service.bulk_delete_transactions(db, data.ids, current_user)
    return {
        "status": "success",
        "message": f"{result['deleted_count']} transaksi berhasil dihapus",
        "data": result,
    }


# ═══════════ DOKUMEN TANDA TANGAN ═══════════

@router.get("/{transaction_id}/document")
def download_document(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    """Download dokumen peminjaman — public (tanpa login)."""
    service = BorrowService()
    tx = service.get_transaction_detail(db, transaction_id)

    # Buat placeholder text yang berisi ringkasan transaksi
    borrower_name = tx.borrower.borrower_name if tx.borrower else "N/A"
    lines = [
        f"DOKUMEN PEMINJAMAN INVENTARIS BMKG",
        f"=" * 50,
        f"",
        f"Nomor Transaksi : #{transaction_id}",
        f"Peminjam        : {borrower_name}",
        f"Tanggal Pinjam  : {tx.borrow_date}",
        f"Rencana Kembali : {tx.expected_return_date}",
        f"Petugas         : {tx.officer.officer_name if tx.officer else '-'}",
        f"Status          : {tx.status}",
        f"",
        f"Unit yang Dipinjam:",
    ]
    for d in tx.details:
        comp_name = d.component.item_name if d.component else "-"
        lines.append(f"  - {comp_name} (Qty: {d.quantity})")
    lines.extend([
        f"",
        f"=" * 50,
        f"",
        f"Tanda Tangan,",
        f"",
        f"",
        f"(_____________________)",
        f"",
        f"Catatan: Dokumen ini perlu ditandatangani oleh peminjam dan petugas.",
        f"Setelah ditandatangani, upload kembali melalui sistem.",
    ])

    output = BytesIO("\n".join(lines).encode("utf-8"))
    return StreamingResponse(
        output,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=peminjaman_{transaction_id}.txt"},
    )


@router.post("/{transaction_id}/document")
def upload_signed_document(
    transaction_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Upload dokumen yang sudah ditandatangani — public (tanpa login) atau authenticated."""
    import os
    import uuid

    # Simpan file ke folder uploads
    upload_dir = os.path.join("uploads", "documents")
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(file.filename or "document.pdf")[1] or ".pdf"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(upload_dir, filename)

    contents = file.file.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    # Simpan path relatif ke database (tanpa "uploads/" prefix, sesuai konvensi existing)
    doc_path = f"documents/{filename}"
    service = BorrowService()
    tx = service.upload_signed_document(db, transaction_id, doc_path, current_user)
    return {"status": "success", "message": "Dokumen tertandatangan berhasil diupload", "data": tx.model_dump()}
