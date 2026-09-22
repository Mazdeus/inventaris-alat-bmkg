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
from app.services.transaction_number_service import generate_transaction_number
from app.services.transaction_snapshot_service import TransactionSnapshotService
from app.core.logging_config import get_logger
from app.core.status_labels import status_label

logger = get_logger()


class BorrowService:
    def __init__(self):
        self.repo = BorrowRepository()
        self.comp_repo = InventoryComponentRepository()
        self.log_svc = ActivityLogService()
        self.snapshot_svc = TransactionSnapshotService()

    # ── Helper ──

    def _build_details(self, tx) -> list[BorrowDetailResponse]:
        """Bangun daftar BorrowDetailResponse dari borrow_details transaksi."""
        details = []
        for d in (tx.borrow_details or []):
            comp = d.inventory_component
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
        return details

    def _to_list_item(self, tx: BorrowTransaction, snapshot_data: dict | None = None) -> BorrowTransactionListResponse:
        if snapshot_data:
            b_data = snapshot_data.get("borrower")
            borrower_type_val = (
                b_data.get("borrower_type")
                if b_data and b_data.get("borrower_type")
                else (
                    (tx.borrower.borrower_type.value if hasattr(tx.borrower.borrower_type, "value") else str(tx.borrower.borrower_type))
                    if tx and tx.borrower and tx.borrower.borrower_type
                    else None
                )
            )
            borrower_obj = BorrowerBrief(
                id=b_data.get("id") or (tx.borrower.id if tx.borrower else 0),
                borrower_name=b_data.get("borrower_name") or b_data.get("name") or (tx.borrower.borrower_name if tx.borrower else ""),
                borrower_type=borrower_type_val,
            ) if (b_data or tx.borrower) else None

            o_data = snapshot_data.get("officer")
            officer_name = (o_data.get("officer_name") or o_data.get("name")) if o_data else (tx.officer.officer_name if tx.officer else None)

            if "details" in snapshot_data and snapshot_data["details"]:
                details = [
                    BorrowDetailResponse(
                        id=d.get("id") or 0,
                        component=ComponentBrief(**d["component"]) if d.get("component") else None,
                        quantity=d.get("quantity") or len(d.get("selected_items") or []),
                        selected_items=[SelectedItemResponse(**it) for it in (d.get("selected_items") or [])],
                    )
                    for d in snapshot_data["details"]
                ]
            else:
                details = self._build_details(tx)
        else:
            borrower_obj = BorrowerBrief.model_validate(tx.borrower) if tx.borrower else None
            officer_name = tx.officer.officer_name if tx.officer else None
            details = self._build_details(tx)

        total_items = sum(d.quantity for d in details)
        return BorrowTransactionListResponse(
            id=tx.id,
            transaction_number=tx.transaction_number,
            daily_sequence=tx.daily_sequence,
            borrower=borrower_obj,
            issued_by=tx.issued_by,
            officer_name=officer_name,
            borrow_date=tx.borrow_date,
            expected_return_date=tx.expected_return_date,
            status=tx.status,
            signed_document=tx.signed_document,
            items_count=len(details),
            total_items=total_items,
            details=details,
            created_at=tx.created_at,
        )

    def _to_detail(self, tx: BorrowTransaction, db: Session) -> BorrowTransactionResponse:
        snap = self.snapshot_svc.get_snapshot(db, "borrow", tx.id)
        snapshot_data = snap.get("snapshot_data") if snap else None

        if snapshot_data:
            b_data = snapshot_data.get("borrower")
            borrower_type_val = (
                b_data.get("borrower_type")
                if b_data and b_data.get("borrower_type")
                else (
                    (tx.borrower.borrower_type.value if hasattr(tx.borrower.borrower_type, "value") else str(tx.borrower.borrower_type))
                    if tx and tx.borrower and tx.borrower.borrower_type
                    else None
                )
            )
            borrower_obj = BorrowerBrief(
                id=b_data.get("id") or (tx.borrower.id if tx.borrower else 0),
                borrower_name=b_data.get("borrower_name") or b_data.get("name") or (tx.borrower.borrower_name if tx.borrower else ""),
                borrower_type=borrower_type_val,
            ) if (b_data or tx.borrower) else None

            o_data = snapshot_data.get("officer")
            officer_obj = OfficerBrief(
                id=o_data.get("id") or 0,
                officer_name=o_data.get("officer_name") or o_data.get("name") or "",
                nip=o_data.get("nip"),
                position=o_data.get("position"),
                institution=o_data.get("institution"),
            ) if o_data else (OfficerBrief.model_validate(tx.officer) if tx.officer else None)

            if "details" in snapshot_data and snapshot_data["details"]:
                details = [
                    BorrowDetailResponse(
                        id=d.get("id") or 0,
                        component=ComponentBrief(**d["component"]) if d.get("component") else None,
                        quantity=d.get("quantity") or len(d.get("selected_items") or []),
                        selected_items=[SelectedItemResponse(**it) for it in (d.get("selected_items") or [])],
                    )
                    for d in snapshot_data["details"]
                ]
            else:
                details = self._build_details(tx)
        else:
            borrower_obj = BorrowerBrief.model_validate(tx.borrower) if tx.borrower else None
            officer_obj = OfficerBrief.model_validate(tx.officer) if tx.officer else None
            details = self._build_details(tx)

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
            ext_summary = None  # graceful fallback

        return BorrowTransactionResponse(
            id=tx.id,
            transaction_number=tx.transaction_number,
            daily_sequence=tx.daily_sequence,
            borrower=borrower_obj,
            officer=officer_obj,
            issued_by=tx.issued_by,
            borrow_date=tx.borrow_date,
            expected_return_date=tx.expected_return_date,
            status=tx.status,
            photo=tx.photo,
            signed_document=tx.signed_document,
            item_description=tx.item_description,
            purpose=tx.purpose,
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
        if borrower.deleted_at is not None:
            raise HTTPException(status_code=400, detail="Peminjam sudah dihapus dan tidak bisa digunakan untuk transaksi baru")

        # validasi setiap detail + SN yang dipilih
        for detail in data.details:
            comp = self.comp_repo.get(db, detail.inventory_component_id)
            if not comp:
                raise HTTPException(status_code=404, detail=f"Unit ID {detail.inventory_component_id} tidak ditemukan")
            if comp.deleted_at is not None:
                raise HTTPException(status_code=400, detail=f"Unit '{comp.item_name}' sudah dihapus dan tidak bisa dipinjam")

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
                    detail=f"Stok tidak mencukupi: '{comp.item_name}'. Diminta {len(item_ids)}, tersedia {available}",
                )

        # Semua peminjaman start dengan status "Menunggu" — menunggu admin approve
        tx_number, tx_seq = generate_transaction_number(db, "borrow")
        tx = BorrowTransaction(
            transaction_number=tx_number,
            daily_sequence=tx_seq,
            borrower_id=data.borrower_id,
            issued_by=data.issued_by if data.issued_by else None,
            borrow_date=data.borrow_date,
            expected_return_date=data.expected_return_date,
            photo=data.photo.strip() if data.photo else None,
            item_description=data.item_description.strip() if data.item_description else None,
            purpose=data.purpose.strip() if data.purpose else None,
            status="Pending",
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
            # Set item ke status Ditahan (id=7) selama status Menunggu
            from app.services.inventory_service import InventoryService
            inv_svc = InventoryService()
            for item_id in item_ids:
                item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
                if item and item.status_id == 1:  # Available → Ditahan
                    item.status_id = 7  # Ditahan
                    inv_svc._write_history(db,
                        item_id=item.id,
                        component_id=item.inventory_component_id,
                        from_status_id=1, to_status_id=7,
                        source="BORROW",
                        borrow_id=tx.id,
                        user_id=current_user.id,
                        notes=f"Barang ditahan untuk pengajuan peminjaman #{tx.transaction_number or tx.id}",
                    )

        db.commit()

        db.refresh(tx)

        logger.info("Peminjaman %s dibuat oleh %s (peminjam=%s)", tx.transaction_number or tx.id, current_user.full_name, data.borrower_id)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} membuat peminjaman #{tx.id} (Menunggu persetujuan)",
                         reference_table="borrow_transactions", reference_id=tx.id,
                         reference_path=f"/borrow/transactions/{tx.id}")

        return self._to_detail(self.repo.get_with_details(db, tx.id), db)

    # ── Read ──

    def get_transactions(self, db: Session, *, current_user: User | None = None, page=1, size=10, **filters):
        skip = (page - 1) * size
        txs = self.repo.get_filtered(db, skip=skip, limit=size, **filters)
        total = self.repo.count_filtered(db, **filters)
        if not txs:
            return [], total

        from app.models.transaction_snapshot import TransactionSnapshot
        snapshots = (
            db.query(TransactionSnapshot)
            .filter(
                TransactionSnapshot.transaction_type == "borrow",
                TransactionSnapshot.transaction_id.in_([t.id for t in txs]),
            )
            .all()
        )
        snap_map = {s.transaction_id: s.snapshot_data for s in snapshots if s.snapshot_data}
        return [self._to_list_item(tx, snapshot_data=snap_map.get(tx.id)) for tx in txs], total


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
        if tx.status != "Pending":
            raise HTTPException(status_code=409, detail="Hanya transaksi dengan status Menunggu yang bisa disetujui")

        if not tx.signed_document:
            raise HTTPException(status_code=409, detail="Dokumen tertandatangan harus diunggah terlebih dahulu sebelum menyetujui peminjaman")

        # Validasi ulang: semua item yang dipilih masih Ditahan (milik transaksi ini)
        for detail in tx.borrow_details:
            for bdi in detail.borrow_detail_items:
                item = bdi.inventory_item
                if item.status_id != 7:  # Not Ditahan — mungkin sudah diambil transaksi lain
                    raise HTTPException(
                        status_code=409,
                        detail=f"Item SN '{item.serial_number or '-'}' pada unit '{detail.inventory_component.item_name}' "
                               f"sudah tidak tersedia (status: {item.status.status_name if item.status else 'N/A'})",
                    )

        # Set status ke Borrowed
        tx.status = "Borrowed"

        # Mark item yang dipilih sebagai "Borrowed" dan catat riwayat
        from app.services.inventory_service import InventoryService
        inv_svc = InventoryService()
        for detail in tx.borrow_details:
            for bdi in detail.borrow_detail_items:
                item = bdi.inventory_item
                if item.status_id == 7:  # Ditahan → Borrowed
                    item.status_id = 2  # Borrowed
                    # Catat riwayat status
                    inv_svc._write_history(db,
                        item_id=item.id,
                        component_id=item.inventory_component_id,
                        from_status_id=7, to_status_id=2,
                        source="BORROW",
                        borrow_id=tx.id,
                        user_id=current_user.id,
                        notes=f"Peminjaman #{tx.transaction_number or tx.id} disetujui",
                    )


        db.commit()
        db.refresh(tx)

        logger.info("Peminjaman %s disetujui oleh %s", tx.transaction_number or transaction_id, current_user.full_name)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} menyetujui peminjaman #{transaction_id}",
                         reference_table="borrow_transactions", reference_id=tx.id,
                         reference_path=f"/borrow/transactions/{tx.id}")

        return self._to_detail(self.repo.get_with_details(db, tx.id), db)

    def reject_borrow(self, db: Session, transaction_id: int, reason: str | None, current_user: User) -> BorrowTransactionResponse:
        tx = self.repo.get_with_details(db, transaction_id)
        if not tx:
            raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
        if tx.status != "Pending":
            raise HTTPException(status_code=409, detail="Hanya transaksi dengan status Menunggu yang bisa ditolak")

        # Kembalikan item dari Ditahan ke Available
        from app.services.inventory_service import InventoryService
        inv_svc = InventoryService()
        for detail in tx.borrow_details:
            for bdi in detail.borrow_detail_items:
                item = bdi.inventory_item
                if item.status_id == 7:  # Ditahan → Available
                    item.status_id = 1  # Available
                    inv_svc._write_history(db,
                        item_id=item.id, component_id=item.inventory_component_id,
                        from_status_id=7, to_status_id=1,
                        source="BORROW", borrow_id=tx.id,
                        user_id=current_user.id,
                    )

        tx.status = "Cancelled"
        self.snapshot_svc.create_borrow_snapshot(db, tx, archived_by=current_user.id)
        db.commit()
        db.refresh(tx)

        logger.info("Peminjaman %s ditolak oleh %s", tx.transaction_number or transaction_id, current_user.full_name)

        log_msg = f"{current_user.full_name} menolak peminjaman #{transaction_id}"
        if reason:
            log_msg += f". {reason}"
        self.log_svc.log(db, user_id=current_user.id, activity=log_msg,
                         reference_table="borrow_transactions", reference_id=tx.id,
                         reference_path=f"/borrow/transactions/{tx.id}")

        return self._to_detail(self.repo.get_with_details(db, tx.id), db)

    def cancel_borrow(self, db: Session, transaction_id: int, current_user: User) -> BorrowTransactionResponse:
        """Batalkan transaksi yang sedang Dipinjam — Admin only."""
        tx = self.repo.get_with_details(db, transaction_id)
        if not tx:
            raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
        if tx.status != "Borrowed":
            raise HTTPException(status_code=409, detail="Hanya transaksi dengan status Dipinjam yang bisa dibatalkan")

        tx.status = "Cancelled"
        self._return_selected_items_to_available(db, tx)
        # Catat riwayat status untuk setiap item
        from app.services.inventory_service import InventoryService
        inv_svc = InventoryService()
        for d in tx.borrow_details:
            for bdi in d.borrow_detail_items:
                item = bdi.inventory_item
                if item.status_id == 1 and item.status:  # seharusnya Available setelah _return
                    inv_svc._write_history(db,
                        item_id=item.id,
                        component_id=item.inventory_component_id,
                        from_status_id=2, to_status_id=1,  # Borrowed → Available
                        source="BORROW",
                        borrow_id=tx.id,
                        user_id=current_user.id,
                    )
        self.snapshot_svc.create_borrow_snapshot(db, tx, archived_by=current_user.id)
        db.commit()
        db.refresh(tx)

        logger.info("Peminjaman %s dibatalkan oleh %s", tx.transaction_number or transaction_id, current_user.full_name)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} membatalkan peminjaman #{transaction_id}",
                         reference_table="borrow_transactions", reference_id=tx.id,
                         reference_path=f"/borrow/transactions/{tx.id}")

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

    # ── Update ──

    def update_borrow(self, db: Session, transaction_id: int, data, current_user: User) -> BorrowTransactionResponse:
        """Update transaksi peminjaman.
        - Status Menunggu: boleh edit peminjam, tanggal, petugas, dan daftar barang.
        - Status Dipinjam: hanya boleh edit tanggal rencana kembali & petugas (metadata).
        - Status Dikembalikan / Dibatalkan: tidak bisa diedit."""
        tx = self.repo.get_with_details(db, transaction_id)
        if not tx:
            raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")

        if tx.status not in ("Pending", "Borrowed"):
            raise HTTPException(
                status_code=409,
                detail=f"Transaksi dengan status '{status_label(tx.status)}' tidak bisa diedit. "
                       f"Hanya status Menunggu dan Dipinjam yang bisa diedit.",
            )

        from app.services.inventory_service import InventoryService
        inv_svc = InventoryService()
        update_data = data.model_dump(exclude_unset=True)

        is_pending = tx.status == "Pending"

        # Validasi & update metadata
        if "borrow_date" in update_data and update_data["borrow_date"] is not None:
            if not is_pending:
                raise HTTPException(status_code=400, detail="Tanggal pinjam hanya bisa diubah saat status Menunggu")
            tx.borrow_date = update_data["borrow_date"]

        if "expected_return_date" in update_data and update_data["expected_return_date"] is not None:
            tx.expected_return_date = update_data["expected_return_date"]

        if "issued_by" in update_data:
            tx.issued_by = update_data["issued_by"] if update_data["issued_by"] else None

        if "borrower_id" in update_data and update_data["borrower_id"] is not None:
            if not is_pending:
                raise HTTPException(status_code=400, detail="Peminjam hanya bisa diubah saat status Menunggu")
            borrower = db.query(Borrower).filter(Borrower.id == update_data["borrower_id"]).first()
            if not borrower:
                raise HTTPException(status_code=404, detail="Data peminjam tidak ditemukan")
            if borrower.deleted_at is not None:
                raise HTTPException(status_code=400, detail="Peminjam sudah dihapus dan tidak bisa digunakan")
            tx.borrower_id = update_data["borrower_id"]

        if "photo" in update_data:
            tx.photo = update_data["photo"].strip() if update_data["photo"] else None

        # Deskripsi & tujuan barang — hanya bisa diubah saat Pending
        if "item_description" in update_data and update_data["item_description"] is not None:
            if not is_pending:
                raise HTTPException(status_code=400, detail="Deskripsi barang hanya bisa diubah saat status Menunggu")
            tx.item_description = update_data["item_description"].strip()

        if "purpose" in update_data and update_data["purpose"] is not None:
            if not is_pending:
                raise HTTPException(status_code=400, detail="Tujuan barang hanya bisa diubah saat status Menunggu")
            tx.purpose = update_data["purpose"].strip()

        # Validasi tanggal: expected_return_date >= borrow_date
        if tx.expected_return_date < tx.borrow_date:
            raise HTTPException(status_code=422, detail="Tanggal rencana pengembalian harus >= tanggal peminjaman")

        # Update daftar barang (hanya Pending)
        if data.details is not None:
            if not is_pending:
                raise HTTPException(status_code=400, detail="Daftar barang hanya bisa diubah saat status Menunggu")

            new_details = data.details
            if not new_details:
                raise HTTPException(status_code=400, detail="Minimal 1 unit harus dipilih")

            # Validasi setiap detail baru (data.details adalah objek Pydantic, bukan dict)
            for detail in new_details:
                comp = self.comp_repo.get(db, detail.inventory_component_id)
                if not comp:
                    raise HTTPException(status_code=404, detail=f"Unit ID {detail.inventory_component_id} tidak ditemukan")
                item_ids = detail.inventory_item_ids
                if not item_ids:
                    raise HTTPException(status_code=400, detail="inventory_item_ids wajib diisi (minimal 1 SN)")
                for item_id in item_ids:
                    item = db.query(InventoryItem).filter(
                        InventoryItem.id == item_id,
                        InventoryItem.inventory_component_id == detail.inventory_component_id,
                    ).first()
                    if not item:
                        raise HTTPException(status_code=404, detail=f"Item ID {item_id} tidak ditemukan pada unit '{comp.item_name}'")
                    # Item baru harus Available, atau sudah milik transaksi ini (Ditahan)
                    is_owned = any(
                        item_id == bdi.inventory_item_id
                        for d in (tx.borrow_details or [])
                        for bdi in (d.borrow_detail_items or [])
                    )
                    if item.status_id != 1 and not is_owned:
                        raise HTTPException(
                            status_code=409,
                            detail=f"Item SN '{item.serial_number or '-'}' pada unit '{comp.item_name}' tidak tersedia",
                        )

            # Kembalikan semua item lama dari Ditahan → Available
            for d in (tx.borrow_details or []):
                for bdi in (d.borrow_detail_items or []):
                    item = bdi.inventory_item
                    if item and item.status_id == 7:  # Ditahan → Available
                        item.status_id = 1
                        inv_svc._write_history(db,
                            item_id=item.id, component_id=item.inventory_component_id,
                            from_status_id=7, to_status_id=1,
                            source="BORROW", borrow_id=tx.id, user_id=current_user.id,
                        )

            # Hapus borrow_detail_items & borrow_details lama
            for d in list(tx.borrow_details or []):
                for bdi in list(d.borrow_detail_items or []):
                    db.delete(bdi)
                db.delete(d)
            db.flush()

            # Buat borrow_details baru + borrow_detail_items
            for detail in new_details:
                qty = len(detail.inventory_item_ids)
                bd = BorrowDetail(
                    borrow_id=tx.id,
                    inventory_component_id=detail.inventory_component_id,
                    quantity=qty,
                )
                db.add(bd)
                db.flush()
                for item_id in detail.inventory_item_ids:
                    db.add(BorrowDetailItem(borrow_detail_id=bd.id, inventory_item_id=item_id))
                    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
                    if item and item.status_id == 1:  # Available → Ditahan
                        item.status_id = 7

        db.commit()
        db.refresh(tx)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} memperbarui peminjaman #{transaction_id}",
                         reference_table="borrow_transactions", reference_id=tx.id,
                         reference_path=f"/borrow/transactions/{tx.id}")

        return self._to_detail(self.repo.get_with_details(db, tx.id), db)

    # ── Bulk Delete ──

    def bulk_delete_transactions(self, db: Session, ids: list[int], current_user: User) -> dict:
        """Hapus transaksi secara massal. Hanya transaksi status Pending yang bisa dihapus."""
        txs = self.repo.get_by_ids(db, ids)

        if not txs:
            raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")

        # Pisahkan ID yang boleh dihapus vs yang diblokir
        deletable_ids = []
        blocked_ids = []
        for tx in txs:
            if tx.status == "Pending":
                deletable_ids.append(tx.id)
            else:
                blocked_ids.append(tx.id)

        if blocked_ids:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Beberapa transaksi tidak bisa dihapus. Hanya transaksi berstatus 'Menunggu' yang bisa dihapus.",
                    "blocked_ids": blocked_ids,
                },
            )

        if not deletable_ids:
            raise HTTPException(status_code=400, detail="Tidak ada transaksi yang bisa dihapus")

        # Kembalikan item dari Ditahan → Available untuk transaksi Menunggu
        from app.services.inventory_service import InventoryService
        inv_svc = InventoryService()
        txs_to_delete = [tx for tx in txs if tx.id in deletable_ids]
        for tx in txs_to_delete:
            if tx.status == "Pending":
                for detail in tx.borrow_details:
                    for bdi in detail.borrow_detail_items:
                        item = bdi.inventory_item
                        if item and item.status_id == 7:  # Ditahan → Available
                            item.status_id = 1
                            inv_svc._write_history(db,
                                item_id=item.id, component_id=item.inventory_component_id,
                                from_status_id=7, to_status_id=1,
                                source="BORROW", borrow_id=tx.id, user_id=current_user.id,
                            )
        db.flush()

        # Update item_status_history: set borrow_transaction_id ke NULL agar riwayat tetap ada
        from app.models.item_status_history import ItemStatusHistory
        for h in db.query(ItemStatusHistory).filter(
            ItemStatusHistory.borrow_transaction_id.in_(deletable_ids)
        ).all():
            if not h.notes:
                h.notes = f"Transaksi peminjaman #{h.borrow_transaction_id} telah dihapus"
            else:
                h.notes = f"{h.notes} | Transaksi peminjaman #{h.borrow_transaction_id} telah dihapus"
            h.borrow_transaction_id = None
        db.flush()

        # Update item_status_history: set return_id ke NULL untuk return yang terkait
        from app.models.return_ import Return as ReturnModel
        linked_return_ids = [
            r[0] for r in db.query(ReturnModel.id).filter(ReturnModel.borrow_id.in_(deletable_ids)).all()
        ]
        if linked_return_ids:
            for h in db.query(ItemStatusHistory).filter(
                ItemStatusHistory.return_id.in_(linked_return_ids)
            ).all():
                if not h.notes:
                    h.notes = f"Pengembalian #{h.return_id} telah dihapus"
                else:
                    h.notes = f"{h.notes} | Pengembalian #{h.return_id} telah dihapus"
                h.return_id = None
            db.flush()

        # Hapus terkait: return_detail_items → return_details → returns → borrow_detail_items → borrow_details → activity_logs → transaksi
        self.repo.delete_return_detail_items_by_transaction_ids(db, deletable_ids)
        self.repo.delete_return_details_by_transaction_ids(db, deletable_ids)
        self.repo.delete_returns_by_transaction_ids(db, deletable_ids)
        self.repo.delete_borrow_detail_items_by_transaction_ids(db, deletable_ids)
        self.repo.delete_details_by_transaction_ids(db, deletable_ids)
        self.repo.delete_activity_logs_by_transaction_ids(db, deletable_ids)
        deleted_count = self.repo.delete_by_ids(db, deletable_ids)

        db.commit()

        logger.info("%d transaksi peminjaman dihapus massal oleh %s", deleted_count, current_user.full_name)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} menghapus {deleted_count} transaksi peminjaman secara massal (IDs: {deletable_ids})",
                         reference_table="borrow_transactions", reference_id=None)

        return {"deleted_count": deleted_count, "deleted_ids": deletable_ids}

    # ── Signed Document ──

    def upload_signed_document(self, db: Session, transaction_id: int, document_path: str, current_user: User) -> BorrowTransactionResponse:
        """Upload dokumen yang sudah ditandatangani. Hanya untuk transaksi status Pending."""
        tx = self.repo.get(db, transaction_id)
        if not tx:
            raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")

        if tx.status != "Pending":
            raise HTTPException(status_code=400, detail=f"Upload dokumen hanya bisa dilakukan saat status Menunggu. Status saat ini: {status_label(tx.status)}.")

        tx.signed_document = document_path
        db.commit()
        db.refresh(tx)

        user_name = current_user.full_name
        user_id_val = current_user.id
        logger.info("Dokumen peminjaman %s diupload oleh %s", tx.transaction_number or transaction_id, user_name)
        self.log_svc.log(db, user_id=user_id_val,
                         activity=f"{user_name} mengupload dokumen tertandatangan untuk peminjaman #{transaction_id}",
                         reference_table="borrow_transactions", reference_id=tx.id,
                         reference_path=f"/borrow/transactions/{tx.id}")

        return self._to_detail(self.repo.get_with_details(db, tx.id), db)

    def upload_signed_document_public(self, db: Session, transaction_id: int, document_path: str) -> BorrowTransactionResponse:
        """Upload dokumen tanda tangan — publik (tanpa login)."""
        tx = self.repo.get(db, transaction_id)
        if not tx:
            raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")

        if tx.status != "Pending":
            raise HTTPException(status_code=400, detail=f"Upload dokumen hanya bisa dilakukan saat status Menunggu. Status saat ini: {status_label(tx.status)}.")

        tx.signed_document = document_path
        db.commit()
        db.refresh(tx)

        self.log_svc.log(db, user_id=None,
                         activity=f"Upload dokumen tertandatangan untuk peminjaman #{transaction_id} (public)",
                         reference_table="borrow_transactions", reference_id=tx.id,
                         reference_path=f"/borrow/transactions/{tx.id}")

        return self._to_detail(self.repo.get_with_details(db, tx.id), db)

    def get_signed_document_path(self, db: Session, transaction_id: int) -> str | None:
        """Ambil path dokumen tertandatangan."""
        tx = self.repo.get(db, transaction_id)
        if not tx:
            raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
        return tx.signed_document
