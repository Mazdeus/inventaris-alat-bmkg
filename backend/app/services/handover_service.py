"""HandoverService — logika bisnis transaksi pelimpahan ke UPT."""
from datetime import date as dt_date, datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.handover import Handover
from app.models.handover_item import HandoverItem
from app.models.inventory_item import InventoryItem
from app.models.inventory_component import InventoryComponent
from app.models.inventory_status import InventoryStatus
from app.models.user import User
from app.schemas.handover import (
    HandoverCreate, HandoverItemResponse, HandoverListResponse, HandoverResponse,
)
from app.services.activity_log_service import ActivityLogService
from app.services.inventory_service import InventoryService
from app.core.upload import delete_upload


class HandoverService:
    def __init__(self):
        self.log_svc = ActivityLogService()
        self.inv_svc = InventoryService()

    def _to_list_item(self, h: Handover) -> HandoverListResponse:
        items_count = len(h.items) if h.items else 0
        return HandoverListResponse(
            id=h.id,
            upt_receiver=h.upt_receiver,
            handover_date=h.handover_date,
            status=h.status,
            items_count=items_count,
            officer_name=h.officer.officer_name if h.officer else None,
            created_at=h.created_at,
        )

    def _to_detail(self, h: Handover) -> HandoverResponse:
        items = []
        for hi in (h.items or []):
            item = hi.inventory_item
            comp = item.component if item else None
            items.append(HandoverItemResponse(
                id=hi.id,
                inventory_item_id=hi.inventory_item_id,
                serial_number=item.serial_number if item else None,
                component_name=comp.item_name if comp else "",
            ))
        return HandoverResponse(
            id=h.id,
            upt_receiver=h.upt_receiver,
            issued_by=h.issued_by,
            officer_name=h.officer.officer_name if h.officer else None,
            handover_date=h.handover_date,
            status=h.status,
            photo=h.photo,
            signed_document=h.signed_document,
            notes=h.notes,
            items=items,
            created_at=h.created_at,
            completed_at=h.completed_at,
        )

    def _get_status_id(self, db: Session, status_name: str) -> int:
        st = db.query(InventoryStatus).filter(InventoryStatus.status_name == status_name).first()
        if not st:
            raise HTTPException(status_code=500, detail=f"Status '{status_name}' tidak ditemukan di database")
        return st.id

    # ── Create ──

    def create_handover(self, db: Session, data: HandoverCreate, current_user: User) -> HandoverResponse:
        # Validasi setiap item
        for it in data.items:
            item = db.query(InventoryItem).filter(InventoryItem.id == it.inventory_item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail=f"Item ID {it.inventory_item_id} tidak ditemukan")
            if item.status_id != 1:  # Available only
                status_name = item.status.status_name if item.status else "N/A"
                raise HTTPException(
                    status_code=409,
                    detail=f"Item SN '{item.serial_number or '-'}' tidak tersedia untuk pelimpahan (status: {status_name})",
                )

        h = Handover(
            upt_receiver=data.upt_receiver.strip(),
            issued_by=data.issued_by if data.issued_by else None,
            handover_date=data.handover_date,
            photo=data.photo.strip() if data.photo else None,
            notes=data.notes.strip() if data.notes else None,
            status="Draft",
        )
        db.add(h)
        db.flush()

        ditahan_id = self._get_status_id(db, "Ditahan")

        for it in data.items:
            db.add(HandoverItem(
                handover_id=h.id,
                inventory_item_id=it.inventory_item_id,
            ))
            # Set item ke Ditahan selama Draft
            item = db.query(InventoryItem).filter(InventoryItem.id == it.inventory_item_id).first()
            if item:
                old_status_id = item.status_id
                item.status_id = ditahan_id
                self.inv_svc._write_history(db,
                    item_id=item.id, component_id=item.inventory_component_id,
                    from_status_id=old_status_id, to_status_id=ditahan_id,
                    source="HANDOVER", user_id=current_user.id,
                )

        db.commit()
        db.refresh(h)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} membuat pelimpahan #{h.id} ke UPT '{h.upt_receiver}' (Draft)",
                         reference_table="handovers", reference_id=h.id)

        return self._to_detail(h)

    # ── Read ──

    def get_handovers(
        self, db: Session, *,
        page: int = 1, size: int = 10,
        search: str | None = None, status: str | None = None,
    ):
        from sqlalchemy import func
        query = db.query(Handover)
        if search:
            query = query.filter(Handover.upt_receiver.ilike(f"%{search}%"))
        if status:
            query = query.filter(Handover.status == status)

        total = db.query(func.count(Handover.id))
        if search:
            total = total.filter(Handover.upt_receiver.ilike(f"%{search}%"))
        if status:
            total = total.filter(Handover.status == status)
        total = total.scalar() or 0

        skip = (page - 1) * size
        handovers = query.order_by(Handover.id.desc()).offset(skip).limit(size).all()

        return [self._to_list_item(h) for h in handovers], total

    def get_handover_detail(self, db: Session, handover_id: int) -> HandoverResponse:
        h = db.query(Handover).filter(Handover.id == handover_id).first()
        if not h:
            raise HTTPException(status_code=404, detail="Pelimpahan tidak ditemukan")
        return self._to_detail(h)

    # ── Complete (Draft → Dilimpahkan) ──

    def complete_handover(self, db: Session, handover_id: int, current_user: User) -> HandoverResponse:
        h = db.query(Handover).filter(Handover.id == handover_id).first()
        if not h:
            raise HTTPException(status_code=404, detail="Pelimpahan tidak ditemukan")
        if h.status != "Draft":
            raise HTTPException(status_code=409, detail="Hanya pelimpahan dengan status Draft yang bisa dilimpahkan")

        if not h.signed_document:
            raise HTTPException(status_code=409, detail="Dokumen tertandatangan harus diunggah terlebih dahulu sebelum melimpahkan")

        dilimpahkan_id = self._get_status_id(db, "Dilimpahkan")
        ditahan_id = self._get_status_id(db, "Ditahan")

        # Kumpulkan component yang terpengaruh untuk update quantity
        affected_components: dict[int, int] = {}  # component_id → count

        # Ubah status setiap item jadi Dilimpahkan
        for hi in (h.items or []):
            item = hi.inventory_item
            cid = item.inventory_component_id
            old_status_id = item.status_id
            item.status_id = dilimpahkan_id
            affected_components[cid] = affected_components.get(cid, 0) + 1
            # Catat history
            self.inv_svc._write_history(db,
                item_id=item.id, component_id=cid,
                from_status_id=old_status_id, to_status_id=dilimpahkan_id,
                source="HANDOVER", user_id=current_user.id,
            )

        # Kurangi total_quantity setiap komponen yang terdampak
        from app.models.inventory_component import InventoryComponent
        for cid, count in affected_components.items():
            comp = db.query(InventoryComponent).filter(InventoryComponent.id == cid).first()
            if comp:
                comp.total_quantity = max(0, comp.total_quantity - count)

        h.status = "Dilimpahkan"
        h.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(h)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} menyelesaikan pelimpahan #{handover_id} ke UPT '{h.upt_receiver}'",
                         reference_table="handovers", reference_id=h.id)

        return self._to_detail(h)

    # ── Cancel (Draft → Dibatalkan) ──

    def cancel_handover(self, db: Session, handover_id: int, current_user: User) -> HandoverResponse:
        h = db.query(Handover).filter(Handover.id == handover_id).first()
        if not h:
            raise HTTPException(status_code=404, detail="Pelimpahan tidak ditemukan")
        if h.status != "Draft":
            raise HTTPException(status_code=409, detail="Hanya pelimpahan dengan status Draft yang bisa dibatalkan")

        available_id = self._get_status_id(db, "Available")
        ditahan_id = self._get_status_id(db, "Ditahan")

        # Kembalikan item dari Ditahan ke Available
        for hi in (h.items or []):
            item = hi.inventory_item
            if item and item.status_id == ditahan_id:
                old_id = item.status_id
                item.status_id = available_id
                self.inv_svc._write_history(db,
                    item_id=item.id, component_id=item.inventory_component_id,
                    from_status_id=old_id, to_status_id=available_id,
                    source="HANDOVER", user_id=current_user.id,
                )

        h.status = "Dibatalkan"
        db.commit()
        db.refresh(h)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} membatalkan pelimpahan #{handover_id} ke UPT '{h.upt_receiver}'",
                         reference_table="handovers", reference_id=h.id)

        return self._to_detail(h)

    # ── Dokumen ──

    def upload_signed_document(self, db: Session, handover_id: int, document_path: str, current_user: User) -> HandoverResponse:
        h = db.query(Handover).filter(Handover.id == handover_id).first()
        if not h:
            raise HTTPException(status_code=404, detail="Pelimpahan tidak ditemukan")

        if h.status != "Draft":
            raise HTTPException(status_code=400, detail=f"Upload dokumen hanya bisa saat status Draft. Status saat ini: {h.status}")

        h.signed_document = document_path
        db.commit()
        db.refresh(h)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} mengupload dokumen untuk pelimpahan #{handover_id}",
                         reference_table="handovers", reference_id=h.id)

        return self._to_detail(h)

    def upload_signed_document_public(self, db: Session, handover_id: int, document_path: str) -> HandoverResponse:
        """Upload dokumen tanpa login — untuk public upload."""
        h = db.query(Handover).filter(Handover.id == handover_id).first()
        if not h:
            raise HTTPException(status_code=404, detail="Pelimpahan tidak ditemukan")

        if h.status != "Draft":
            raise HTTPException(status_code=400, detail=f"Upload dokumen hanya bisa saat status Draft. Status saat ini: {h.status}")

        h.signed_document = document_path
        db.commit()
        db.refresh(h)

        self.log_svc.log(db, user_id=None,
                         activity=f"Upload dokumen untuk pelimpahan #{handover_id} (public)",
                         reference_table="handovers", reference_id=h.id)

        return self._to_detail(h)

    # ── Update ──

    def update_handover(self, db: Session, handover_id: int, data, current_user: User) -> HandoverResponse:
        """Update pelimpahan. Hanya status Draft yang bisa diedit."""
        h = db.query(Handover).filter(Handover.id == handover_id).first()
        if not h:
            raise HTTPException(status_code=404, detail="Pelimpahan tidak ditemukan")

        if h.status != "Draft":
            raise HTTPException(
                status_code=409,
                detail=f"Pelimpahan dengan status '{h.status}' tidak bisa diedit. Hanya status Draft yang bisa diedit.",
            )

        update_data = data.model_dump(exclude_unset=True)

        if "upt_receiver" in update_data and update_data["upt_receiver"] is not None:
            h.upt_receiver = update_data["upt_receiver"].strip()
        if "issued_by" in update_data:
            h.issued_by = update_data["issued_by"] if update_data["issued_by"] else None
        if "handover_date" in update_data and update_data["handover_date"] is not None:
            h.handover_date = update_data["handover_date"]
        if "photo" in update_data:
            h.photo = update_data["photo"].strip() if update_data["photo"] else None
        if "notes" in update_data:
            h.notes = update_data["notes"].strip() if update_data["notes"] else None

        # Update daftar barang (Draft only)
        if "items" in update_data and update_data["items"] is not None:
            new_items = update_data["items"]
            if not new_items:
                raise HTTPException(status_code=400, detail="Minimal 1 barang harus dipilih")

            available_id = self._get_status_id(db, "Available")
            ditahan_id = self._get_status_id(db, "Ditahan")

            # Kembalikan item lama dari Ditahan → Available
            for hi in list(h.items or []):
                item = hi.inventory_item
                if item and item.status_id == ditahan_id:
                    item.status_id = available_id
                    self.inv_svc._write_history(db,
                        item_id=item.id, component_id=item.inventory_component_id,
                        from_status_id=ditahan_id, to_status_id=available_id,
                        source="HANDOVER", user_id=current_user.id,
                    )
                db.delete(hi)
            db.flush()

            # Tambah item baru → Ditahan
            for it in new_items:
                item = db.query(InventoryItem).filter(InventoryItem.id == it["inventory_item_id"]).first()
                if not item:
                    raise HTTPException(status_code=404, detail=f"Item ID {it['inventory_item_id']} tidak ditemukan")
                if item.status_id != available_id:
                    status_name = item.status.status_name if item.status else "N/A"
                    raise HTTPException(
                        status_code=409,
                        detail=f"Item SN '{item.serial_number or '-'}' tidak tersedia untuk pelimpahan (status: {status_name})",
                    )
                db.add(HandoverItem(handover_id=h.id, inventory_item_id=item.id))
                old_status_id = item.status_id
                item.status_id = ditahan_id
                self.inv_svc._write_history(db,
                    item_id=item.id, component_id=item.inventory_component_id,
                    from_status_id=old_status_id, to_status_id=ditahan_id,
                    source="HANDOVER", user_id=current_user.id,
                )

        db.commit()
        db.refresh(h)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} memperbarui pelimpahan #{handover_id}",
                         reference_table="handovers", reference_id=h.id)

        return self._to_detail(h)

    # ── Delete ──

    def delete_handover(self, db: Session, handover_id: int, current_user: User) -> dict:
        """Hapus pelimpahan. Hanya status Draft yang bisa dihapus.
        Untuk Draft: kembalikan item dari Ditahan ke Available."""
        h = db.query(Handover).filter(Handover.id == handover_id).first()
        if not h:
            raise HTTPException(status_code=404, detail="Pelimpahan tidak ditemukan")

        if h.status != "Draft":
            raise HTTPException(
                status_code=409,
                detail=f"Pelimpahan dengan status '{h.status}' tidak bisa dihapus. Hanya Draft yang bisa dihapus.",
            )

        hid = h.id
        upt = h.upt_receiver

        # Untuk Draft: kembalikan item dari Ditahan ke Available
        if h.status == "Draft":
            available_id = self._get_status_id(db, "Available")
            ditahan_id = self._get_status_id(db, "Ditahan")
            for hi in (h.items or []):
                item = hi.inventory_item
                if item and item.status_id == ditahan_id:
                    item.status_id = available_id
                    self.inv_svc._write_history(db,
                        item_id=item.id, component_id=item.inventory_component_id,
                        from_status_id=ditahan_id, to_status_id=available_id,
                        source="HANDOVER", user_id=current_user.id,
                    )

        # Hapus file dokumen jika ada
        if h.signed_document:
            delete_upload(h.signed_document)

        db.delete(h)  # cascade: handover_items via relationship cascade="all, delete-orphan"
        db.commit()

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} menghapus pelimpahan #{hid} ke UPT '{upt}'",
                         reference_table="handovers", reference_id=hid)

        return {"status": "success", "message": f"Pelimpahan #{hid} berhasil dihapus"}
