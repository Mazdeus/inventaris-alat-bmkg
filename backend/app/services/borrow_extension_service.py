"""BorrowExtensionService — logika bisnis perpanjangan peminjaman."""
from datetime import date as dt_date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.borrow_extension import BorrowExtension
from app.models.borrow_transaction import BorrowTransaction
from app.models.user import User
from app.schemas.borrow_extension import BorrowExtensionCreate, BorrowExtensionResponse
from app.services.activity_log_service import ActivityLogService


class BorrowExtensionService:
    def __init__(self):
        self.log_svc = ActivityLogService()

    def _to_response(self, ext: BorrowExtension) -> BorrowExtensionResponse:
        return BorrowExtensionResponse(
            id=ext.id,
            borrow_id=ext.borrow_id,
            requested_by=ext.requested_by,
            requested_by_name=ext.requester.full_name if ext.requester else None,
            requested_return_date=ext.requested_return_date,
            reason=ext.reason,
            status=ext.status,
            approved_by=ext.approved_by,
            approved_by_name=ext.approver.full_name if ext.approver else None,
            approved_at=ext.approved_at,
            created_at=ext.created_at,
        )

    def get_extensions_by_borrow(self, db: Session, borrow_id: int) -> list[BorrowExtensionResponse]:
        exts = (
            db.query(BorrowExtension)
            .filter(BorrowExtension.borrow_id == borrow_id)
            .order_by(BorrowExtension.created_at.desc())
            .all()
        )
        return [self._to_response(e) for e in exts]

    def request_extension(self, db: Session, borrow_id: int, data: BorrowExtensionCreate,
                          current_user: User) -> BorrowExtensionResponse:
        tx = db.query(BorrowTransaction).filter(BorrowTransaction.id == borrow_id).first()
        if not tx:
            raise HTTPException(status_code=404, detail="Transaksi peminjaman tidak ditemukan")
        if tx.status != "Borrowed":
            raise HTTPException(status_code=409, detail="Hanya transaksi dengan status Dipinjam yang bisa diperpanjang")

        # Cek apakah sudah ada perpanjangan
        existing = (
            db.query(BorrowExtension)
            .filter(BorrowExtension.borrow_id == borrow_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Transaksi ini sudah memiliki perpanjangan (status: {existing.status}). "
                       f"Maksimal 1 perpanjangan per transaksi.",
            )

        today = dt_date.today()
        if today > tx.expected_return_date:
            raise HTTPException(
                status_code=409,
                detail="Perpanjangan hanya bisa diajukan sebelum tanggal rencana kembali berlalu.",
            )

        if data.requested_return_date <= tx.expected_return_date:
            raise HTTPException(
                status_code=422,
                detail=f"Tanggal perpanjangan ({data.requested_return_date}) harus lebih besar "
                       f"dari rencana kembali saat ini ({tx.expected_return_date}).",
            )

        if not data.reason or not data.reason.strip():
            raise HTTPException(status_code=422, detail="Alasan perpanjangan wajib diisi")

        ext = BorrowExtension(
            borrow_id=borrow_id,
            requested_by=current_user.id,
            requested_return_date=data.requested_return_date,
            reason=data.reason.strip(),
            status="Pending",
        )
        db.add(ext)
        db.commit()
        db.refresh(ext)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} mengajukan perpanjangan peminjaman #{borrow_id} "
                                  f"ke {data.requested_return_date}",
                         reference_table="borrow_extensions", reference_id=ext.id)

        return self._to_response(ext)

    def approve_extension(self, db: Session, borrow_id: int, extension_id: int,
                          current_user: User) -> BorrowExtensionResponse:
        ext = db.query(BorrowExtension).filter(
            BorrowExtension.id == extension_id,
            BorrowExtension.borrow_id == borrow_id,
        ).first()
        if not ext:
            raise HTTPException(status_code=404, detail="Pengajuan perpanjangan tidak ditemukan")
        if ext.status != "Pending":
            raise HTTPException(status_code=409, detail="Hanya perpanjangan dengan status Menunggu yang bisa disetujui")

        # Update transaksi
        tx = db.query(BorrowTransaction).filter(BorrowTransaction.id == borrow_id).first()
        old_date = tx.expected_return_date
        tx.expected_return_date = ext.requested_return_date

        # Update extension
        ext.status = "Approved"
        ext.approved_by = current_user.id
        from datetime import datetime
        ext.approved_at = datetime.utcnow()

        db.commit()
        db.refresh(ext)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} menyetujui perpanjangan peminjaman #{borrow_id} "
                                  f"({old_date} → {ext.requested_return_date})",
                         reference_table="borrow_extensions", reference_id=ext.id)

        return self._to_response(ext)

    def reject_extension(self, db: Session, borrow_id: int, extension_id: int,
                         current_user: User) -> BorrowExtensionResponse:
        ext = db.query(BorrowExtension).filter(
            BorrowExtension.id == extension_id,
            BorrowExtension.borrow_id == borrow_id,
        ).first()
        if not ext:
            raise HTTPException(status_code=404, detail="Pengajuan perpanjangan tidak ditemukan")
        if ext.status != "Pending":
            raise HTTPException(status_code=409, detail="Hanya perpanjangan dengan status Menunggu yang bisa ditolak")

        ext.status = "Rejected"
        ext.approved_by = current_user.id
        from datetime import datetime
        ext.approved_at = datetime.utcnow()

        db.commit()
        db.refresh(ext)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} menolak perpanjangan peminjaman #{borrow_id}",
                         reference_table="borrow_extensions", reference_id=ext.id)

        return self._to_response(ext)
