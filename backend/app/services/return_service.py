"""ReturnService — logika bisnis pengembalian inventaris. (FR-23 s.d FR-27)"""
from datetime import date as dt_date
from io import BytesIO

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.models.borrow_transaction import BorrowTransaction
from app.models.inventory_component import InventoryComponent
from app.models.inventory_item import InventoryItem
from app.models.inventory_status import InventoryStatus
from app.models.return_ import Return
from app.models.return_detail import ReturnDetail
from app.models.return_detail_item import ReturnDetailItem
from app.models.user import User
from app.repositories.return_repository import ReturnRepository
from app.schemas.return_ import (
    ReturnCreate, ReturnDetailItemResponse, ReturnDetailResponse,
    ReturnListResponse, ReturnResponse,
)
from app.services.activity_log_service import ActivityLogService
from app.services.inventory_service import InventoryService
from app.core.upload import delete_upload


class ReturnService:
    def __init__(self):
        self.repo = ReturnRepository()
        self.log_svc = ActivityLogService()

    def _find_status_id(self, db: Session, name: str) -> int:
        s = db.query(InventoryStatus).filter(InventoryStatus.status_name == name).first()
        if not s:
            raise HTTPException(status_code=500, detail=f"Status '{name}' tidak ditemukan di database")
        return s.id

    def _compute_late(self, ret: Return) -> tuple[bool, int]:
        """Hitung apakah pengembalian terlambat dan berapa hari."""
        tx = ret.borrow_transaction
        if not tx or not tx.expected_return_date:
            return False, 0
        if ret.return_date > tx.expected_return_date:
            delta = (ret.return_date - tx.expected_return_date).days
            return True, delta
        return False, 0

    def _to_list_item(self, ret: Return) -> ReturnListResponse:
        tx = ret.borrow_transaction
        details = ret.return_details or []
        is_late, days_late = self._compute_late(ret)
        return ReturnListResponse(
            id=ret.id,
            borrow_transaction_id=tx.id if tx else None,
            borrower_name=tx.borrower.borrower_name if tx and tx.borrower else "",
            received_by=ret.received_by,
            officer_name=ret.officer.officer_name if ret.officer else "",
            return_date=ret.return_date,
            expected_return_date=tx.expected_return_date if tx else None,
            status=ret.status,
            is_late=is_late,
            days_late=days_late,
            items_count=len(details),
            total_items=sum(d.quantity for d in details),
        )

    def _to_detail(self, ret: Return) -> ReturnResponse:
        tx = ret.borrow_transaction
        detail_list = []
        for d in (ret.return_details or []):
            comp = d.inventory_component
            # Ambil detail per barang fisik
            items = []
            for rdi in (d.return_detail_items or []):
                inv_item = rdi.inventory_item
                items.append(ReturnDetailItemResponse(
                    id=rdi.id,
                    inventory_item_id=rdi.inventory_item_id,
                    serial_number=inv_item.serial_number if inv_item else None,
                    condition=rdi.condition,
                    notes=rdi.notes,
                    status_after=inv_item.status.status_name if inv_item and inv_item.status else "",
                ))
            detail_list.append(ReturnDetailResponse(
                id=d.id,
                component={"id": comp.id, "item_name": comp.item_name, "serial_number": comp.serial_number} if comp else None,
                quantity=d.quantity,
                items=items,
            ))
        is_late, days_late = self._compute_late(ret)
        # Ambil ringkasan perpanjangan dari transaksi asal
        ext_summary = None
        try:
            exts = tx.extensions if tx else []
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
            ext_summary = None
        return ReturnResponse(
            id=ret.id,
            borrow_transaction_id=tx.id if tx else None,
            borrow_id=ret.borrow_id,
            borrower_name=tx.borrower.borrower_name if tx and tx.borrower else "",
            received_by=ret.received_by,
            officer_name=ret.officer.officer_name if ret.officer else "",
            return_date=ret.return_date,
            borrow_date=tx.borrow_date if tx else None,
            expected_return_date=tx.expected_return_date if tx else None,
            is_late=is_late,
            days_late=days_late,
            status=ret.status,
            photo=ret.photo,
            signed_document=ret.signed_document,
            late_reason=ret.late_reason,
            details=detail_list,
            transaction_status=tx.status if tx else None,
            created_at=ret.verified_at,
            extension=ext_summary,  # menggunakan verified_at sebagai timestamp audit
        )

    # ── Read ──

    def get_returns(self, db: Session, *, page=1, size=10, start_date=None, end_date=None):
        skip = (page - 1) * size
        rets = self.repo.get_filtered(db, start_date=start_date, end_date=end_date, skip=skip, limit=size)
        total = self.repo.count(db)
        return [self._to_list_item(r) for r in rets], total

    def get_return_detail(self, db: Session, return_id: int) -> ReturnResponse:
        ret = self.repo.get_with_details(db, return_id)
        if not ret:
            raise HTTPException(status_code=404, detail="Data pengembalian tidak ditemukan")
        return self._to_detail(ret)

    def get_return_by_id(self, db: Session, return_id: int) -> Return | None:
        return self.repo.get(db, return_id)

    # ── Create ──

    def create_return(self, db: Session, data: ReturnCreate, current_user: User) -> ReturnResponse:
        # validasi borrow
        tx = db.query(BorrowTransaction).filter(BorrowTransaction.id == data.borrow_id).first()
        if not tx:
            raise HTTPException(status_code=404, detail="Transaksi peminjaman tidak ditemukan")
        if tx.status != "Dipinjam":
            raise HTTPException(status_code=409, detail="Transaksi belum disetujui, sudah dikembalikan, atau dibatalkan")
        if data.return_date < tx.borrow_date:
            raise HTTPException(status_code=422, detail="Tanggal kembali tidak boleh sebelum tanggal pinjam")

        # Validasi keterlambatan
        if data.return_date > tx.expected_return_date:
            if not data.late_reason or not data.late_reason.strip():
                raise HTTPException(status_code=422, detail="Alasan keterlambatan wajib diisi karena pengembalian terlambat")

        # Validasi catatan kerusakan: wajib jika kondisi rusak
        for detail in data.details:
            for item in detail.items:
                is_damaged = item.condition.lower() not in ("baik", "bagus", "normal")
                if is_damaged and not (item.notes or "").strip():
                    # Ambil SN item untuk pesan error
                    inv_item = db.query(InventoryItem).filter(
                        InventoryItem.id == item.inventory_item_id
                    ).first()
                    sn = inv_item.serial_number if inv_item else f"#{item.inventory_item_id}"
                    raise HTTPException(
                        status_code=422,
                        detail=f"Catatan kerusakan wajib diisi untuk barang {sn}",
                    )

        # Validasi: semua item yang dipinjam harus dikembalikan
        # Kumpulkan semua inventory_item_id yang dipinjam dari borrow_detail_items
        borrowed_item_ids: set[int] = set()
        for detail in tx.borrow_details:
            for bdi in detail.borrow_detail_items:
                borrowed_item_ids.add(bdi.inventory_item_id)

        # Kumpulkan semua inventory_item_id yang akan dikembalikan
        returned_item_ids: set[int] = set()
        for detail in data.details:
            for item in detail.items:
                returned_item_ids.add(item.inventory_item_id)

        # Pastikan semua yang dipinjam dikembalikan
        missing = borrowed_item_ids - returned_item_ids
        if missing:
            # Ambil info SN yang belum dikembalikan
            missing_items = db.query(InventoryItem).filter(InventoryItem.id.in_(missing)).all()
            missing_sns = [it.serial_number or f"#{it.id}" for it in missing_items]
            raise HTTPException(
                status_code=409,
                detail=f"Semua barang yang dipinjam harus dikembalikan. "
                        f"Barang yang belum dikembalikan: {', '.join(missing_sns[:5])}"
                        f"{' dan lainnya' if len(missing_sns) > 5 else ''}",
            )

        # Pastikan tidak ada item asing yang bukan milik transaksi ini
        extra = returned_item_ids - borrowed_item_ids
        if extra:
            extra_items = db.query(InventoryItem).filter(InventoryItem.id.in_(extra)).all()
            extra_sns = [it.serial_number or f"#{it.id}" for it in extra_items]
            raise HTTPException(
                status_code=409,
                detail=f"Barang berikut bukan milik transaksi ini: {', '.join(extra_sns)}",
            )

        # Validasi setiap item ada dan terkait komponen yang benar
        for detail in data.details:
            comp = db.query(InventoryComponent).filter(
                InventoryComponent.id == detail.inventory_component_id
            ).first()
            if not comp:
                raise HTTPException(status_code=404, detail=f"Komponen ID {detail.inventory_component_id} tidak ditemukan")
            for item in detail.items:
                inv_item = db.query(InventoryItem).filter(
                    InventoryItem.id == item.inventory_item_id,
                    InventoryItem.inventory_component_id == detail.inventory_component_id,
                ).first()
                if not inv_item:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Item ID {item.inventory_item_id} tidak ditemukan pada komponen '{comp.item_name}'",
                    )

        # Buat return
        ret = Return(
            borrow_id=data.borrow_id,
            received_by=data.received_by if data.received_by else None,
            photo=data.photo.strip() if data.photo else None,
            return_date=data.return_date,
            late_reason=data.late_reason.strip() if data.late_reason else None,
            status="Menunggu",
        )
        db.add(ret)
        db.flush()

        for detail_data in data.details:
            cid = detail_data.inventory_component_id

            # Buat ReturnDetail per komponen
            rd = ReturnDetail(
                return_id=ret.id,
                inventory_component_id=cid,
                quantity=len(detail_data.items),
            )
            db.add(rd)
            db.flush()

            # Buat ReturnDetailItem per barang fisik
            for item_data in detail_data.items:
                db.add(ReturnDetailItem(
                    return_detail_id=rd.id,
                    inventory_item_id=item_data.inventory_item_id,
                    condition=item_data.condition,
                    notes=item_data.notes,
                ))
            # Note: status item TIDAK diubah di sini — tetap Dipinjam sampai diverifikasi.

        # Status peminjaman tetap Dipinjam sampai pengembalian diverifikasi.
        db.commit()
        db.refresh(ret)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} membuat pengembalian #{ret.id} (Menunggu)",
                         reference_table="returns", reference_id=ret.id)

        return self._to_detail(self.repo.get_with_details(db, ret.id))

    # ── Delete ──

    def delete_return(self, db: Session, return_id: int, current_user: User) -> dict:
        """Hapus pengembalian. Hanya status 'Menunggu' yang bisa dihapus.
        Karena status barang belum diubah, peminjaman tetap Dipinjam."""
        ret = self.repo.get_with_details(db, return_id)
        if not ret:
            raise HTTPException(status_code=404, detail="Data pengembalian tidak ditemukan")

        if ret.status != "Menunggu":
            raise HTTPException(status_code=409, detail=f"Hanya pengembalian dengan status 'Menunggu' yang bisa dihapus. Status saat ini: {ret.status}")

        tx = ret.borrow_transaction
        borrow_id = tx.id if tx else None

        # Hapus file dokumen jika ada
        if ret.signed_document:
            delete_upload(ret.signed_document)

        # Hapus return_details terlebih dahulu (FK NOT NULL pada return_id)
        for rd in list(ret.return_details):
            db.delete(rd)
        db.flush()

        ret_id = ret.id
        db.delete(ret)
        db.commit()

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} menghapus pengembalian #{ret_id}",
                         reference_table="returns", reference_id=ret_id)

        return {"status": "success", "message": f"Pengembalian #{ret_id} berhasil dihapus."}

    # ── Update ──

    def update_return(self, db: Session, return_id: int, data, current_user: User) -> ReturnResponse:
        """Update pengembalian. Hanya status 'Menunggu' yang bisa diedit."""
        ret = self.repo.get_with_details(db, return_id)
        if not ret:
            raise HTTPException(status_code=404, detail="Data pengembalian tidak ditemukan")

        if ret.status != "Menunggu":
            raise HTTPException(
                status_code=409,
                detail=f"Hanya pengembalian dengan status 'Menunggu' yang bisa diedit. Status saat ini: {ret.status}",
            )

        tx = ret.borrow_transaction
        if not tx:
            raise HTTPException(status_code=404, detail="Transaksi peminjaman terkait tidak ditemukan")

        update_data = data.model_dump(exclude_unset=True)

        if "received_by" in update_data:
            ret.received_by = update_data["received_by"] if update_data["received_by"] else None

        if "return_date" in update_data and update_data["return_date"] is not None:
            if update_data["return_date"] < tx.borrow_date:
                raise HTTPException(status_code=422, detail="Tanggal kembali tidak boleh sebelum tanggal pinjam")
            ret.return_date = update_data["return_date"]

        if "late_reason" in update_data:
            ret.late_reason = update_data["late_reason"].strip() if update_data["late_reason"] else None

        if "photo" in update_data:
            ret.photo = update_data["photo"].strip() if update_data["photo"] else None

        # Validasi keterlambatan
        if ret.return_date > tx.expected_return_date:
            if not ret.late_reason or not ret.late_reason.strip():
                raise HTTPException(status_code=422, detail="Alasan keterlambatan wajib diisi karena pengembalian terlambat")

        # Update kondisi per barang
        if "details" in update_data and update_data["details"] is not None:
            # Map inventory_item_id → ReturnDetailItem dari data yang sudah dimuat
            rdi_by_item: dict[int, ReturnDetailItem] = {}
            for rd in (ret.return_details or []):
                for rdi in (rd.return_detail_items or []):
                    rdi_by_item[rdi.inventory_item_id] = rdi

            for detail_data in update_data["details"]:
                for item_data in detail_data["items"]:
                    is_damaged = item_data["condition"].lower() not in ("baik", "bagus", "normal")
                    if is_damaged and not (item_data.get("notes") or "").strip():
                        inv_item = db.query(InventoryItem).filter(
                            InventoryItem.id == item_data["inventory_item_id"]
                        ).first()
                        sn = inv_item.serial_number if inv_item else f"#{item_data['inventory_item_id']}"
                        raise HTTPException(
                            status_code=422,
                            detail=f"Catatan kerusakan wajib diisi untuk barang {sn}",
                        )
                    rdi = rdi_by_item.get(item_data["inventory_item_id"])
                    if rdi:
                        rdi.condition = item_data["condition"]
                        rdi.notes = item_data.get("notes")

        db.commit()
        db.refresh(ret)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} memperbarui pengembalian #{return_id}",
                         reference_table="returns", reference_id=ret.id)

        return self._to_detail(self.repo.get_with_details(db, ret.id))

    # ── Dokumen ──

    def download_document(self, db: Session, return_id: int):
        """Download template dokumen pengembalian."""
        ret = self.repo.get_with_details(db, return_id)
        if not ret:
            raise HTTPException(status_code=404, detail="Data pengembalian tidak ditemukan")

        tx = ret.borrow_transaction
        borrower_name = tx.borrower.borrower_name if tx and tx.borrower else "N/A"
        officer_name = ret.officer.officer_name if ret.officer else "-"

        lines = [
            f"DOKUMEN PENGEMBALIAN INVENTARIS BMKG",
            f"=" * 50,
            f"",
            f"Nomor Pengembalian : #{return_id}",
            f"Nomor Transaksi    : #{ret.borrow_id}",
            f"Peminjam           : {borrower_name}",
            f"Tanggal Pinjam     : {tx.borrow_date if tx else '-'}",
            f"Rencana Kembali    : {tx.expected_return_date if tx else '-'}",
            f"Tanggal Kembali    : {ret.return_date}",
            f"Petugas Penerima   : {officer_name}",
            f"Status Pengembalian: {ret.status}",
            f"",
            f"Unit yang Dikembalikan:",
        ]
        for d in (ret.return_details or []):
            comp = d.inventory_component
            comp_name = comp.item_name if comp else "-"
            lines.append(f"  - {comp_name} (Qty: {d.quantity})")
            for rdi in (d.return_detail_items or []):
                inv_item = rdi.inventory_item
                sn = inv_item.serial_number if inv_item else "-"
                lines.append(f"      SN: {sn}  |  Kondisi: {rdi.condition}")
                if rdi.notes:
                    lines.append(f"      Catatan: {rdi.notes}")

        if ret.late_reason:
            lines.extend([
                f"",
                f"Alasan Keterlambatan: {ret.late_reason}",
            ])

        lines.extend([
            f"",
            f"=" * 50,
            f"",
            f"Tanda Tangan,",
            f"",
            f"",
            f"Peminjam                    Petugas Penerima",
            f"",
            f"(_____________________)      (_____________________)",
            f"",
            f"Catatan: Dokumen ini perlu ditandatangani oleh peminjam dan petugas.",
            f"Setelah ditandatangani, upload kembali melalui sistem.",
        ])

        output = BytesIO("\n".join(lines).encode("utf-8"))
        return StreamingResponse(
            output,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=pengembalian_{return_id}.txt"},
        )

    def upload_signed_document(self, db: Session, return_id: int, document_path: str,
                               current_user) -> ReturnResponse:
        """Upload dokumen pengembalian yang sudah ditandatangani. Hanya untuk status Menunggu."""
        ret = self.repo.get(db, return_id)
        if not ret:
            raise HTTPException(status_code=404, detail="Data pengembalian tidak ditemukan")

        if ret.status != "Menunggu":
            raise HTTPException(status_code=400, detail=f"Upload dokumen hanya bisa dilakukan saat status Menunggu. Status saat ini: {ret.status}.")

        ret.signed_document = document_path
        db.commit()
        db.refresh(ret)

        user_name = current_user.full_name
        user_id_val = current_user.id
        self.log_svc.log(db, user_id=user_id_val,
                         activity=f"{user_name} mengupload dokumen tertandatangan untuk pengembalian #{return_id}",
                         reference_table="returns", reference_id=ret.id)

        return self._to_detail(self.repo.get_with_details(db, return_id))

    # ── Verifikasi ──

    def verify_return(self, db: Session, return_id: int, current_user: User) -> ReturnResponse:
        """Admin menyetujui pengembalian — ubah status barang sesuai kondisi dan tandai Selesai."""
        ret = self.repo.get_with_details(db, return_id)
        if not ret:
            raise HTTPException(status_code=404, detail="Data pengembalian tidak ditemukan")
        if ret.status == "Selesai":
            raise HTTPException(status_code=409, detail="Pengembalian sudah diverifikasi sebelumnya")
        if ret.status != "Menunggu":
            raise HTTPException(status_code=409, detail=f"Hanya pengembalian dengan status 'Menunggu' yang bisa diverifikasi (current: {ret.status})")

        tx = ret.borrow_transaction
        if not tx:
            raise HTTPException(status_code=404, detail="Transaksi peminjaman terkait tidak ditemukan")

        if not ret.signed_document:
            raise HTTPException(status_code=409, detail="Dokumen tertandatangan harus diunggah terlebih dahulu sebelum memverifikasi pengembalian")

        from datetime import datetime
        available_id = self._find_status_id(db, "Available")
        broken_id = self._find_status_id(db, "Broken")

        affected_component_ids = set()
        total_broken = 0
        broken_comps = {}
        inv_svc = InventoryService()

        for rd in ret.return_details:
            for rdi in rd.return_detail_items:
                item = rdi.inventory_item
                if item:
                    old_status_id = item.status_id
                    cond_lower = rdi.condition.lower()
                    new_id = available_id if cond_lower in ("baik", "bagus", "normal") else broken_id
                    item.status_id = new_id
                    affected_component_ids.add(item.inventory_component_id)

                    inv_svc._write_history(db,
                        item_id=item.id,
                        component_id=item.inventory_component_id,
                        from_status_id=old_status_id,
                        to_status_id=new_id,
                        source="RETURN",
                        return_id=ret.id,
                        borrow_id=tx.id,
                        notes=rdi.notes if rdi.notes else None,
                    )

                    if cond_lower not in ("baik", "bagus", "normal"):
                        total_broken += 1
                        cid = item.inventory_component_id
                        if cid not in broken_comps:
                            comp = db.query(InventoryComponent).filter(InventoryComponent.id == cid).first()
                            broken_comps[cid] = {"item_name": comp.item_name if comp else f"#{cid}", "count": 0}
                        broken_comps[cid]["count"] += 1

        tx.status = "Dikembalikan"
        for cid in affected_component_ids:
            inv_svc.recompute_component_status(db, cid)

        ret.status = "Selesai"
        ret.verified_at = datetime.utcnow()
        db.commit()
        db.refresh(ret)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} memverifikasi pengembalian #{return_id}",
                         reference_table="returns", reference_id=ret.id)

        if total_broken > 0:
            import json
            broken_details = [
                {"item_name": v["item_name"], "quantity": v["count"]}
                for v in broken_comps.values()
            ]
            self.log_svc.log(db, user_id=current_user.id,
                             activity=f"{total_broken} item rusak dicatat dalam pengembalian #{ret.id}",
                             reference_table="returns", reference_id=ret.id,
                             extra_data=json.dumps(broken_details, ensure_ascii=False))

        return self._to_detail(self.repo.get_with_details(db, ret.id))

    def reject_return(self, db: Session, return_id: int, current_user: User) -> ReturnResponse:
        """Admin menolak pengembalian — batalkan return, peminjaman tetap Dipinjam."""
        ret = self.repo.get(db, return_id)
        if not ret:
            raise HTTPException(status_code=404, detail="Data pengembalian tidak ditemukan")
        if ret.status != "Menunggu":
            raise HTTPException(status_code=409, detail=f"Hanya pengembalian dengan status 'Menunggu' yang bisa ditolak (current: {ret.status})")

        ret.status = "Dibatalkan"
        db.commit()
        db.refresh(ret)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} menolak pengembalian #{return_id}",
                         reference_table="returns", reference_id=ret.id)

        return self._to_detail(self.repo.get_with_details(db, ret.id))
