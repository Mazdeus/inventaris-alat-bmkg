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
from app.services.transaction_number_service import generate_transaction_number
from app.services.transaction_snapshot_service import TransactionSnapshotService
from app.core.logging_config import get_logger
from app.core.upload import delete_upload

logger = get_logger()


class HandoverService:
    def __init__(self):
        self.log_svc = ActivityLogService()
        self.inv_svc = InventoryService()
        self.snapshot_svc = TransactionSnapshotService()

    def _to_list_item(self, h: Handover, snapshot_data: dict | None = None) -> HandoverListResponse:
        items_count = len(h.items) if h.items else 0
        if snapshot_data:
            o_data = snapshot_data.get("officer")
            officer_name = (o_data.get("officer_name") or o_data.get("name")) if o_data else (h.officer.officer_name if h.officer else None)
            recipient_name = snapshot_data.get("recipient_name") or h.recipient_name
            recipient_nip = snapshot_data.get("recipient_nip") or h.recipient_nip
            if "items" in snapshot_data and snapshot_data["items"]:
                items_count = len(snapshot_data["items"])
        else:
            officer_name = h.officer.officer_name if h.officer else None
            recipient_name = h.recipient_name
            recipient_nip = h.recipient_nip

        return HandoverListResponse(
            id=h.id,
            transaction_number=h.transaction_number,
            daily_sequence=h.daily_sequence,
            upt_receiver=h.upt_receiver,
            recipient_name=recipient_name,
            recipient_nip=recipient_nip,
            handover_date=h.handover_date,
            status=h.status,
            items_count=items_count,
            officer_name=officer_name,
            created_at=h.created_at,
        )

    def _to_detail(self, h: Handover, db: Session | None = None) -> HandoverResponse:
        snapshot_data = None
        if db:
            snap = self.snapshot_svc.get_snapshot(db, "handover", h.id)
            if snap and snap.get("snapshot_data"):
                snapshot_data = snap["snapshot_data"]

        if snapshot_data:
            o_data = snapshot_data.get("officer")
            officer_name = (o_data.get("officer_name") or o_data.get("name")) if o_data else (h.officer.officer_name if h.officer else None)
            upt_id = snapshot_data.get("upt_id") or h.upt_id
            recipient_name = snapshot_data.get("recipient_name") or h.recipient_name
            recipient_nip = snapshot_data.get("recipient_nip") or h.recipient_nip
            if "items" in snapshot_data and snapshot_data["items"]:
                items = [
                    HandoverItemResponse(
                        id=it.get("id") or 0,
                        inventory_item_id=it.get("inventory_item_id") or 0,
                        serial_number=it.get("serial_number"),
                        component_name=it.get("component_name") or "",
                    )
                    for it in snapshot_data["items"]
                ]
            else:
                items = [
                    HandoverItemResponse(
                        id=hi.id,
                        inventory_item_id=hi.inventory_item_id,
                        serial_number=hi.inventory_item.serial_number if hi.inventory_item else None,
                        component_name=hi.inventory_item.component.item_name if (hi.inventory_item and hi.inventory_item.component) else "",
                    )
                    for hi in (h.items or [])
                ]
        else:
            officer_name = h.officer.officer_name if h.officer else None
            upt_id = h.upt_id
            recipient_name = h.recipient_name
            recipient_nip = h.recipient_nip
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
            transaction_number=h.transaction_number,
            daily_sequence=h.daily_sequence,
            upt_receiver=h.upt_receiver,
            upt_id=upt_id,
            recipient_name=recipient_name,
            recipient_nip=recipient_nip,
            issued_by=h.issued_by,
            officer_name=officer_name,
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

        h_number, h_seq = generate_transaction_number(db, "handover")
        h = Handover(
            transaction_number=h_number,
            daily_sequence=h_seq,
            upt_receiver=data.upt_receiver.strip(),
            upt_id=data.upt_id,
            recipient_name=data.recipient_name.strip() if data.recipient_name else None,
            recipient_nip=data.recipient_nip.strip() if data.recipient_nip else None,
            issued_by=data.issued_by if data.issued_by else None,
            handover_date=data.handover_date,
            photo=data.photo.strip() if data.photo else None,
            notes=data.notes.strip() if data.notes else None,
            status="Draft",
        )
        db.add(h)
        db.flush()

        on_hold_id = self._get_status_id(db, "On Hold")

        for it in data.items:
            db.add(HandoverItem(
                handover_id=h.id,
                inventory_item_id=it.inventory_item_id,
            ))
            # Set item ke status On Hold selama Draft
            item = db.query(InventoryItem).filter(InventoryItem.id == it.inventory_item_id).first()
            if item:
                old_status_id = item.status_id
                item.status_id = on_hold_id
                self.inv_svc._write_history(db,
                    item_id=item.id, component_id=item.inventory_component_id,
                    from_status_id=old_status_id, to_status_id=on_hold_id,
                    source="HANDOVER", user_id=current_user.id,
                )

        db.commit()
        db.refresh(h)

        logger.info("Pelimpahan %s ke UPT '%s' dibuat (Draft) oleh %s", h.id, h.upt_receiver, current_user.full_name)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} membuat pelimpahan #{h.id} ke UPT '{h.upt_receiver}' (Draft)",
                         reference_table="handovers", reference_id=h.id)

        return self._to_detail(h)

    # ── Read ──

    def get_handovers(
        self, db: Session, *,
        page: int = 1, size: int = 10,
        search: str | None = None, status: str | None = None,
        start_date: dt_date | None = None, end_date: dt_date | None = None,
        order_dir: str = "desc",
    ):
        from sqlalchemy import func
        query = db.query(Handover)
        if search:
            query = query.filter(Handover.upt_receiver.ilike(f"%{search}%"))
        if status:
            query = query.filter(Handover.status == status)
        if start_date:
            query = query.filter(Handover.handover_date >= start_date)
        if end_date:
            query = query.filter(Handover.handover_date <= end_date)

        total = db.query(func.count(Handover.id))
        if search:
            total = total.filter(Handover.upt_receiver.ilike(f"%{search}%"))
        if status:
            total = total.filter(Handover.status == status)
        if start_date:
            total = total.filter(Handover.handover_date >= start_date)
        if end_date:
            total = total.filter(Handover.handover_date <= end_date)
        total = total.scalar() or 0

        skip = (page - 1) * size
        order_col = Handover.id.asc() if order_dir == "asc" else Handover.id.desc()
        handovers = query.order_by(order_col).offset(skip).limit(size).all()
        if not handovers:
            return [], total

        from app.models.transaction_snapshot import TransactionSnapshot
        snapshots = (
            db.query(TransactionSnapshot)
            .filter(
                TransactionSnapshot.transaction_type == "handover",
                TransactionSnapshot.transaction_id.in_([h.id for h in handovers]),
            )
            .all()
        )
        snap_map = {s.transaction_id: s.snapshot_data for s in snapshots if s.snapshot_data}
        return [self._to_list_item(h, snapshot_data=snap_map.get(h.id)) for h in handovers], total

    def get_handover_detail(self, db: Session, handover_id: int) -> HandoverResponse:
        h = db.query(Handover).filter(Handover.id == handover_id).first()
        if not h:
            raise HTTPException(status_code=404, detail="Pelimpahan tidak ditemukan")
        return self._to_detail(h, db)


    # ── Complete (Draft → Transferred) ──

    def complete_handover(self, db: Session, handover_id: int, current_user: User) -> HandoverResponse:
        h = db.query(Handover).filter(Handover.id == handover_id).first()
        if not h:
            raise HTTPException(status_code=404, detail="Pelimpahan tidak ditemukan")
        if h.status != "Draft":
            raise HTTPException(status_code=409, detail="Hanya pelimpahan dengan status Draft yang bisa dilimpahkan")

        if not h.signed_document:
            raise HTTPException(status_code=409, detail="Dokumen tertandatangan harus diunggah terlebih dahulu sebelum melimpahkan")

        transferred_id = self._get_status_id(db, "Transferred")
        on_hold_id = self._get_status_id(db, "On Hold")

        # Kumpulkan component yang terpengaruh untuk update quantity
        affected_components: dict[int, int] = {}  # component_id → count

        # Ubah status setiap item jadi Transferred
        for hi in (h.items or []):
            item = hi.inventory_item
            cid = item.inventory_component_id
            old_status_id = item.status_id
            item.status_id = transferred_id
            affected_components[cid] = affected_components.get(cid, 0) + 1
            # Catat history
            self.inv_svc._write_history(db,
                item_id=item.id, component_id=cid,
                from_status_id=old_status_id, to_status_id=transferred_id,
                source="HANDOVER", handover_id=h.id, user_id=current_user.id,
                notes=f"Pelimpahan #{h.id} ke UPT {h.upt_receiver}",
            )


        # Kurangi total_quantity setiap komponen yang terdampak
        from app.models.inventory_component import InventoryComponent
        for cid, count in affected_components.items():
            comp = db.query(InventoryComponent).filter(InventoryComponent.id == cid).first()
            if comp:
                comp.total_quantity = max(0, comp.total_quantity - count)

        h.status = "Transferred"
        h.completed_at = datetime.utcnow()
        self.snapshot_svc.create_handover_snapshot(db, h, archived_by=current_user.id)
        db.commit()
        db.refresh(h)

        logger.info("Pelimpahan %s ke UPT '%s' diselesaikan oleh %s", h.id, h.upt_receiver, current_user.full_name)

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
        on_hold_id = self._get_status_id(db, "On Hold")

        # Kembalikan item dari Ditahan ke Available
        for hi in (h.items or []):
            item = hi.inventory_item
            if item and item.status_id == on_hold_id:
                old_id = item.status_id
                item.status_id = available_id
                self.inv_svc._write_history(db,
                    item_id=item.id, component_id=item.inventory_component_id,
                    from_status_id=old_id, to_status_id=available_id,
                    source="HANDOVER", user_id=current_user.id,
                )

        h.status = "Cancelled"
        self.snapshot_svc.create_handover_snapshot(db, h, archived_by=current_user.id)
        db.commit()
        db.refresh(h)

        logger.info("Pelimpahan %s ke UPT '%s' dibatalkan oleh %s", h.id, h.upt_receiver, current_user.full_name)

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

        logger.info("Dokumen pelimpahan %s ke UPT '%s' diupload oleh %s", h.id, h.upt_receiver, current_user.full_name)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} mengupload dokumen untuk pelimpahan #{handover_id}",
                         reference_table="handovers", reference_id=h.id,
                         reference_path=f"/handovers/{h.id}")

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
        if "upt_id" in update_data:
            h.upt_id = update_data["upt_id"]
        if "recipient_name" in update_data:
            h.recipient_name = update_data["recipient_name"].strip() if update_data["recipient_name"] else None
        if "recipient_nip" in update_data:
            h.recipient_nip = update_data["recipient_nip"].strip() if update_data["recipient_nip"] else None
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
            on_hold_id = self._get_status_id(db, "On Hold")

            # Kembalikan item lama dari Ditahan → Available
            for hi in list(h.items or []):
                item = hi.inventory_item
                if item and item.status_id == on_hold_id:
                    item.status_id = available_id
                    self.inv_svc._write_history(db,
                        item_id=item.id, component_id=item.inventory_component_id,
                        from_status_id=on_hold_id, to_status_id=available_id,
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
                item.status_id = on_hold_id
                self.inv_svc._write_history(db,
                    item_id=item.id, component_id=item.inventory_component_id,
                    from_status_id=old_status_id, to_status_id=on_hold_id,
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
            on_hold_id = self._get_status_id(db, "On Hold")
            for hi in (h.items or []):
                item = hi.inventory_item
                if item and item.status_id == on_hold_id:
                    item.status_id = available_id
                    self.inv_svc._write_history(db,
                        item_id=item.id, component_id=item.inventory_component_id,
                        from_status_id=on_hold_id, to_status_id=available_id,
                        source="HANDOVER", user_id=current_user.id,
                    )

        # Hapus file dokumen jika ada
        if h.signed_document:
            delete_upload(h.signed_document)

        db.delete(h)  # cascade: handover_items via relationship cascade="all, delete-orphan"
        db.commit()

        logger.info("Pelimpahan %s ke UPT '%s' dihapus oleh %s", hid, upt, current_user.full_name)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} menghapus pelimpahan #{hid} ke UPT '{upt}'",
                         reference_table="handovers", reference_id=hid)

        return {"status": "success", "message": f"Pelimpahan #{hid} berhasil dihapus"}
