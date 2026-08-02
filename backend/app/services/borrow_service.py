"""BorrowService — logika bisnis transaksi peminjaman. (FR-15 s.d FR-22, FR-27)"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.borrow_detail import BorrowDetail
from app.models.borrow_detail_item import BorrowDetailItem
from app.models.borrow_transaction import BorrowTransaction
from app.models.borrower import Borrower
from app.models.inventory_item import InventoryItem
from app.models.user import User
from app.repositories.borrow_repository import BorrowRepository
from app.repositories.inventory_component_repository import InventoryComponentRepository
from app.schemas.borrow import (
    BorrowDetailResponse, BorrowTransactionCreate, BorrowTransactionListResponse,
    BorrowTransactionResponse, ComponentBrief, BorrowerBrief, OfficerBrief,
    SelectedItemResponse,
)
from app.services.activity_log_service import ActivityLogService


class BorrowService:
    def __init__(self):
        self.repo = BorrowRepository()
        self.comp_repo = InventoryComponentRepository()
        self.log_svc = ActivityLogService()

    # ── Helper ──

    def _to_list_item(self, tx: BorrowTransaction) -> BorrowTransactionListResponse:
        details = tx.borrow_details or []
        total_items = sum(d.quantity for d in details)
        return BorrowTransactionListResponse(
            id=tx.id,
            borrower=BorrowerBrief.model_validate(tx.borrower) if tx.borrower else None,
            issued_by=tx.issued_by,
            officer_name=tx.officer.officer_name if tx.officer else None,
            borrow_date=tx.borrow_date,
            expected_return_date=tx.expected_return_date,
            status=tx.status,
            signed_document=tx.signed_document,
            items_count=len(details),
            total_items=total_items,
            created_at=tx.created_at,
        )

    def _to_detail(self, tx: BorrowTransaction, db: Session) -> BorrowTransactionResponse:
        details = []
        for d in (tx.borrow_details or []):
            comp = d.inventory_component
            # Ambil selected items dari borrow_detail_items (jika ada)
            selected_items = []
            for bdi in (d.borrow_detail_items or []):
                item = bdi.inventory_item
                selected_items.append(SelectedItemResponse(
                    id=item.id,
                    serial_number=item.serial_number,
                ))
            details.append(BorrowDetailResponse(
                id=d.id,
                component=ComponentBrief(
                    id=comp.id, item_name=comp.item_name,
                    brand=comp.brand, model=comp.model,
                    serial_number=comp.serial_number,
                    total_quantity=comp.total_quantity,
                    status=comp.status.status_name if comp.status else "",
                ) if comp else None,
                quantity=d.quantity,
                selected_items=selected_items,
            ))
        # Sertakan ringkasan perpanjangan jika ada (maks 1)
        ext_summary = None
        try:
            exts = tx.extensions or []
            if exts:
                for ext in exts:
                    ext_summary = {
                        "id": ext.id,
                        "status": ext.status,
                        "new_date": ext.requested_return_date.isoformat() if ext.requested_return_date else None,
                        "reason": ext.reason,
                    }
                    break
        except Exception:
            ext_summary = None  # graceful fallback  # hanya satu

        return BorrowTransactionResponse(
            id=tx.id,
            borrower=BorrowerBrief.model_validate(tx.borrower) if tx.borrower else None,
            officer=OfficerBrief.model_validate(tx.officer) if tx.officer else None,
            issued_by=tx.issued_by,
            borrow_date=tx.borrow_date,
            expected_return_date=tx.expected_return_date,
            status=tx.status,
            photo=tx.photo,
            signed_document=tx.signed_document,
            details=details,
            extension=ext_summary,
            created_at=tx.created_at,
        )

    # ── Create ──

    def create_borrow(self, db: Session, data: BorrowTransactionCreate, current_user: User) -> BorrowTransactionResponse:
        # validasi borrower
        borrower = db.query(Borrower).filter(Borrower.id == data.borrower_id).first()
        if not borrower:
            raise HTTPException(status_code=404, detail="Data peminjam tidak ditemukan")

        # validasi setiap detail + SN yang dipilih
        for detail in data.details:
            comp = self.comp_repo.get(db, detail.inventory_component_id)
            if not comp:
                raise HTTPException(status_code=404, detail=f"Unit ID {detail.inventory_component_id} tidak ditemukan")

            item_ids = detail.inventory_item_ids
            if not item_ids:
                raise HTTPException(status_code=400, detail="inventory_item_ids wajib diisi (minimal 1 SN)")

            # Validasi setiap item yang dipilih
            for item_id in item_ids:
                item = db.query(InventoryItem).filter(
                    InventoryItem.id == item_id,
                    InventoryItem.inventory_component_id == detail.inventory_component_id,
                ).first()
                if not item:
                    raise HTTPException(status_code=404, detail=f"Item ID {item_id} tidak ditemukan pada unit '{comp.item_name}'")
                if item.status_id != 1:  # Available
                    raise HTTPException(
                        status_code=409,
                        detail=f"Item SN '{item.serial_number or '-'}' pada unit '{comp.item_name}' tidak tersedia (status: {item.status.status_name if item.status else 'N/A'})",
                    )

            # Pastikan quantity == jumlah SN yang dipilih
            if detail.quantity is not None and detail.quantity != len(item_ids):
                raise HTTPException(
                    status_code=400,
                    detail=f"Quantity ({detail.quantity}) tidak sesuai dengan jumlah SN yang dipilih ({len(item_ids)}) pada unit '{comp.item_name}'",
                )

            # Pastikan tidak melebihi stok Available
            available = self.comp_repo.get_available_quantity(db, comp.id)
            if len(item_ids) > available:
                raise HTTPException(
                    status_code=409,
                    detail=f"Stok tidak mencukupi: '{comp.item_name}' — diminta {len(item_ids)}, tersedia {available}",
                )

        # Semua peminjaman start dengan status "Menunggu" — menunggu admin approve
        tx = BorrowTransaction(
            borrower_id=data.borrower_id,
            issued_by=data.issued_by if data.issued_by else None,
            borrow_date=data.borrow_date,
            expected_return_date=data.expected_return_date,
            photo=data.photo.strip() if data.photo else None,
            status="Menunggu",
        )
        db.add(tx)
        db.flush()

        for detail in data.details:
            item_ids = detail.inventory_item_ids
            qty = detail.quantity or len(item_ids)
            bd = BorrowDetail(
                borrow_id=tx.id,
                inventory_component_id=detail.inventory_component_id,
                quantity=qty,
            )
            db.add(bd)
            db.flush()

            # Simpan item-item yang dipilih ke borrow_detail_items
            for item_id in item_ids:
                db.add(BorrowDetailItem(
                    borrow_detail_id=bd.id,
                    inventory_item_id=item_id,
                ))
            # Item tetap Available selama status Menunggu — hanya berpindah ke Borrowed saat admin approve.

        db.commit()
        db.refresh(tx)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} membuat peminjaman #{tx.id} (Menunggu persetujuan)",
                         reference_table="borrow_transactions", reference_id=tx.id)

        return self._to_detail(self.repo.get_with_details(db, tx.id), db)

    # ── Read ──

    def get_transactions(self, db: Session, *, current_user: User | None = None, page=1, size=10, **filters):
        skip = (page - 1) * size
        txs = self.repo.get_filtered(db, skip=skip, limit=size, **filters)
        total = self.repo.count_filtered(db, **filters)
        return [self._to_list_item(tx) for tx in txs], total

    def get_transaction_detail(self, db: Session, transaction_id: int) -> BorrowTransactionResponse:
        tx = self.repo.get_with_details(db, transaction_id)
        if not tx:
            raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
        return self._to_detail(tx, db)

    # ── Approval ──

    def approve_borrow(self, db: Session, transaction_id: int, current_user: User) -> BorrowTransactionResponse:
        tx = self.repo.get_with_details(db, transaction_id)
        if not tx:
            raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
        if tx.status != "Menunggu":
            raise HTTPException(status_code=409, detail="Hanya transaksi dengan status Menunggu yang bisa disetujui")

        # Validasi ulang: semua item yang dipilih masih Available
        for detail in tx.borrow_details:
            for bdi in detail.borrow_detail_items:
                item = bdi.inventory_item
                if item.status_id != 1:  # Not Available
                    raise HTTPException(
                        status_code=409,
                        detail=f"Item SN '{item.serial_number or '-'}' pada unit '{detail.inventory_component.item_name}' "
                               f"sudah tidak tersedia (status: {item.status.status_name if item.status else 'N/A'})",
                    )

        # Set status ke Dipinjam
        tx.status = "Dipinjam"

        # Mark item yang dipilih sebagai "Borrowed"
        for detail in tx.borrow_details:
            for bdi in detail.borrow_detail_items:
                item = bdi.inventory_item
                if item.status_id == 1:  # Available → Borrowed
                    item.status_id = 2  # Borrowed

        db.commit()
        db.refresh(tx)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} menyetujui peminjaman #{transaction_id}",
                         reference_table="borrow_transactions", reference_id=tx.id)

        return self._to_detail(self.repo.get_with_details(db, tx.id), db)

    def reject_borrow(self, db: Session, transaction_id: int, reason: str | None, current_user: User) -> BorrowTransactionResponse:
        tx = self.repo.get_with_details(db, transaction_id)
        if not tx:
            raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
        if tx.status != "Menunggu":
            raise HTTPException(status_code=409, detail="Hanya transaksi dengan status Menunggu yang bisa ditolak")

        # Item masih Available (belum pernah dipindah ke Borrowed), jadi tidak perlu dikembalikan
        tx.status = "Dibatalkan"
        db.commit()
        db.refresh(tx)

        log_msg = f"{current_user.full_name} menolak peminjaman #{transaction_id}"
        if reason:
            log_msg += f" — {reason}"
        self.log_svc.log(db, user_id=current_user.id, activity=log_msg,
                         reference_table="borrow_transactions", reference_id=tx.id)

        return self._to_detail(self.repo.get_with_details(db, tx.id), db)

    def cancel_borrow(self, db: Session, transaction_id: int, current_user: User) -> BorrowTransactionResponse:
        """Batalkan transaksi yang sedang Dipinjam — Admin only."""
        tx = self.repo.get_with_details(db, transaction_id)
        if not tx:
            raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
        if tx.status != "Dipinjam":
            raise HTTPException(status_code=409, detail="Hanya transaksi dengan status Dipinjam yang bisa dibatalkan")

        tx.status = "Dibatalkan"
        self._return_selected_items_to_available(db, tx)
        db.commit()
        db.refresh(tx)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} membatalkan peminjaman #{transaction_id}",
                         reference_table="borrow_transactions", reference_id=tx.id)

        return self._to_detail(self.repo.get_with_details(db, tx.id), db)

    def _return_selected_items_to_available(self, db: Session, tx) -> None:
        """Kembalikan item yang dipinjam ke status Available (untuk cancel/return)."""
        for d in tx.borrow_details:
            for bdi in d.borrow_detail_items:
                item = bdi.inventory_item
                if item.status_id == 2:  # Borrowed
                    item.status_id = 1  # Available

    def get_selected_items(self, tx) -> dict[int, list[InventoryItem]]:
        """Dapatkan dictionary mapping component_id → list of items per borrow_detail."""
        result = {}
        for d in tx.borrow_details:
            cid = d.inventory_component_id
            if cid not in result:
                result[cid] = []
            for bdi in d.borrow_detail_items:
                result[cid].append(bdi.inventory_item)
        return result

    # ── Bulk Delete ──

    def bulk_delete_transactions(self, db: Session, ids: list[int], current_user: User) -> dict:
        """Hapus transaksi secara massal. Hanya transaksi Dikembalikan & Dibatalkan yang bisa dihapus."""
        txs = self.repo.get_by_ids(db, ids)

        if not txs:
            raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")

        # Pisahkan ID yang boleh dihapus vs yang diblokir
        deletable_ids = []
        blocked_ids = []
        for tx in txs:
            if tx.status in ("Dikembalikan", "Dibatalkan"):
                deletable_ids.append(tx.id)
            else:
                blocked_ids.append(tx.id)

        if blocked_ids:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Beberapa transaksi tidak bisa dihapus karena masih dalam proses (hanya Dikembalikan & Dibatalkan yang bisa dihapus).",
                    "blocked_ids": blocked_ids,
                },
            )

        if not deletable_ids:
            raise HTTPException(status_code=400, detail="Tidak ada transaksi yang bisa dihapus")

        # Hapus terkait: return_details → returns → borrow_detail_items → borrow_details → activity_logs → transaksi
        self.repo.delete_return_details_by_transaction_ids(db, deletable_ids)
        self.repo.delete_returns_by_transaction_ids(db, deletable_ids)
        self.repo.delete_borrow_detail_items_by_transaction_ids(db, deletable_ids)
        self.repo.delete_details_by_transaction_ids(db, deletable_ids)
        self.repo.delete_activity_logs_by_transaction_ids(db, deletable_ids)
        deleted_count = self.repo.delete_by_ids(db, deletable_ids)

        db.commit()

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} menghapus {deleted_count} transaksi peminjaman secara massal (IDs: {deletable_ids})",
                         reference_table="borrow_transactions", reference_id=None)

        return {"deleted_count": deleted_count, "deleted_ids": deletable_ids}

    # ── Signed Document ──

    def upload_signed_document(self, db: Session, transaction_id: int, document_path: str, current_user: User | None) -> BorrowTransactionResponse:
        """Upload dokumen yang sudah ditandatangani — public (current_user bisa None)."""
        tx = self.repo.get(db, transaction_id)
        if not tx:
            raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
        tx.signed_document = document_path
        db.commit()
        db.refresh(tx)

        user_name = current_user.full_name if current_user else "Publik (tanpa login)"
        user_id_val = current_user.id if current_user else None
        self.log_svc.log(db, user_id=user_id_val,
                         activity=f"{user_name} mengupload dokumen tertandatangan untuk peminjaman #{transaction_id}",
                         reference_table="borrow_transactions", reference_id=tx.id)

        return self._to_detail(self.repo.get_with_details(db, tx.id), db)

    def get_signed_document_path(self, db: Session, transaction_id: int) -> str | None:
        """Ambil path dokumen tertandatangan."""
        tx = self.repo.get(db, transaction_id)
        if not tx:
            raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
        return tx.signed_document
