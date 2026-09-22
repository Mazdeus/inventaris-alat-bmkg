"""TransactionSnapshotService — arsip data transaksi selesai ke tabel snapshot.

Tujuan: menyimpan data transaksi saat SELESAI (Dikembalikan/Dibatalkan/Dilimpahkan/
Completed/Cancelled) sehingga perubahan master data (unit, peminjam, petugas) di
kemudian hari TIDAK mengubah tampilan historis transaksi yang sudah selesai.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.transaction_snapshot import TransactionSnapshot


class TransactionSnapshotService:
    def _save(self, db: Session, *, transaction_type: str, transaction_id: int,
              snapshot_data: dict, archived_by: int | None) -> None:
        """Simpan snapshot. Bersifat upsert — replace jika sudah ada untuk transaksi ini."""
        existing = (
            db.query(TransactionSnapshot)
            .filter(
                TransactionSnapshot.transaction_type == transaction_type,
                TransactionSnapshot.transaction_id == transaction_id,
            )
            .first()
        )
        if existing:
            existing.snapshot_data = snapshot_data
            existing.completed_at = datetime.utcnow()
            existing.archived_by = archived_by
        else:
            db.add(TransactionSnapshot(
                transaction_type=transaction_type,
                transaction_id=transaction_id,
                snapshot_data=snapshot_data,
                completed_at=datetime.utcnow(),
                archived_by=archived_by,
            ))

    # ── Peminjaman ──

    # ── Peminjaman ──

    def create_borrow_snapshot(self, db: Session, tx, archived_by: int | None = None) -> None:
        """Snapshot transaksi peminjaman saat selesai/dibatalkan."""
        details_list = []
        for d in (tx.borrow_details or []):
            comp = d.inventory_component
            selected_items = []
            for bdi in (d.borrow_detail_items or []):
                item = bdi.inventory_item
                selected_items.append({
                    "id": item.id if item else None,
                    "serial_number": item.serial_number if item else None,
                })
            details_list.append({
                "id": d.id,
                "component": {
                    "id": comp.id if comp else None,
                    "item_name": comp.item_name if comp else "",
                    "brand": comp.brand if comp else "",
                    "model": comp.model if comp else "",
                    "serial_number": comp.serial_number if comp else None,
                    "total_quantity": comp.total_quantity if comp else 0,
                    "status": comp.status.status_name if comp and comp.status else "",
                } if comp else None,
                "quantity": d.quantity,
                "selected_items": selected_items,
            })

        borrower = tx.borrower
        officer = tx.officer

        b_type = None
        if borrower and borrower.borrower_type:
            b_type = borrower.borrower_type.value if hasattr(borrower.borrower_type, "value") else str(borrower.borrower_type)

        snapshot = {
            "transaction_number": tx.transaction_number,
            "status": tx.status,
            "borrower": {
                "id": borrower.id if borrower else None,
                "borrower_name": borrower.borrower_name if borrower else "",
                "borrower_type": b_type,
                "institution": borrower.institution if borrower else "",
                "nip": borrower.nip if borrower else "",
                "email": borrower.email if borrower else "",
                "phone": borrower.phone if borrower else "",
                "position": borrower.position if borrower else "",
            } if borrower else None,
            "officer": {
                "id": officer.id if officer else None,
                "officer_name": officer.officer_name if officer else "",
                "nip": officer.nip if officer else "",
                "position": officer.position if officer else "",
                "institution": officer.institution if officer else "",
            } if officer else None,
            "issued_by": tx.issued_by,
            "borrow_date": tx.borrow_date.isoformat() if tx.borrow_date else None,
            "expected_return_date": tx.expected_return_date.isoformat() if tx.expected_return_date else None,
            "item_description": tx.item_description,
            "purpose": tx.purpose,
            "photo": tx.photo,
            "signed_document": tx.signed_document,
            "details": details_list,
        }
        self._save(db, transaction_type="borrow", transaction_id=tx.id,
                   snapshot_data=snapshot, archived_by=archived_by)

    # ── Pengembalian ──

    def create_return_snapshot(self, db: Session, ret, archived_by: int | None = None) -> None:
        """Snapshot transaksi pengembalian saat selesai/dibatalkan."""
        tx = ret.borrow_transaction
        borrower = tx.borrower if tx else None

        details_list = []
        for d in (ret.return_details or []):
            comp = d.inventory_component
            items = []
            for rdi in (d.return_detail_items or []):
                inv_item = rdi.inventory_item
                items.append({
                    "id": rdi.id,
                    "inventory_item_id": rdi.inventory_item_id,
                    "serial_number": inv_item.serial_number if inv_item else None,
                    "condition": rdi.condition,
                    "notes": rdi.notes,
                    "status_after": inv_item.status.status_name if inv_item and inv_item.status else "",
                })
            details_list.append({
                "id": d.id,
                "component": {
                    "id": comp.id if comp else None,
                    "item_name": comp.item_name if comp else "",
                    "brand": comp.brand if comp else "",
                    "model": comp.model if comp else "",
                    "serial_number": comp.serial_number if comp else None,
                } if comp else None,
                "quantity": d.quantity,
                "items": items,
            })

        officer = ret.officer

        snapshot = {
            "transaction_number": ret.transaction_number,
            "status": ret.status,
            "borrow_transaction_number": tx.transaction_number if tx else None,
            "borrower_name": borrower.borrower_name if borrower else "",
            "officer": {
                "id": officer.id if officer else None,
                "officer_name": officer.officer_name if officer else "",
                "nip": officer.nip if officer else "",
                "position": officer.position if officer else "",
                "institution": officer.institution if officer else "",
            } if officer else None,
            "return_date": ret.return_date.isoformat() if ret.return_date else None,
            "late_reason": ret.late_reason,
            "photo": ret.photo,
            "signed_document": ret.signed_document,
            "details": details_list,
        }
        self._save(db, transaction_type="return", transaction_id=ret.id,
                   snapshot_data=snapshot, archived_by=archived_by)

    # ── Pelimpahan ──

    def create_handover_snapshot(self, db: Session, h, archived_by: int | None = None) -> None:
        """Snapshot transaksi pelimpahan saat selesai/dibatalkan."""
        items = []
        for hi in (h.items or []):
            item = hi.inventory_item
            comp = item.component if item else None
            items.append({
                "id": hi.id,
                "inventory_item_id": hi.inventory_item_id,
                "component_name": comp.item_name if comp else "",
                "brand": comp.brand if comp else "",
                "model": comp.model if comp else "",
                "serial_number": item.serial_number if item else None,
            })

        officer = h.officer

        snapshot = {
            "upt_receiver": h.upt_receiver,
            "upt_id": getattr(h, "upt_id", None),
            "recipient_name": getattr(h, "recipient_name", None),
            "recipient_nip": getattr(h, "recipient_nip", None),
            "status": h.status,
            "officer": {
                "id": officer.id if officer else None,
                "officer_name": officer.officer_name if officer else "",
                "nip": officer.nip if officer else "",
                "position": officer.position if officer else "",
                "institution": officer.institution if officer else "",
            } if officer else None,
            "handover_date": h.handover_date.isoformat() if h.handover_date else None,
            "notes": h.notes,
            "photo": h.photo,
            "signed_document": h.signed_document,
            "items": items,
        }
        self._save(db, transaction_type="handover", transaction_id=h.id,
                   snapshot_data=snapshot, archived_by=archived_by)

    # ── Perawatan ──

    def create_maintenance_snapshot(self, db: Session, m, archived_by: int | None = None) -> None:
        """Snapshot perawatan saat selesai/dibatalkan."""
        items = []
        for mi in (m.maintenance_items or []):
            item = mi.inventory_item
            items.append({
                "id": mi.id,
                "inventory_item_id": mi.inventory_item_id,
                "serial_number": item.serial_number if item else None,
                "previous_status": mi.previous_status.status_name if mi.previous_status else "",
            })

        comp = m.inventory_component
        officer = m.officer

        snapshot = {
            "status": m.status,
            "component": {
                "id": comp.id if comp else None,
                "item_name": comp.item_name if comp else "",
                "brand": comp.brand if comp else "",
                "model": comp.model if comp else "",
                "serial_number": comp.serial_number if comp else None,
                "status": comp.status.status_name if comp and comp.status else "",
            } if comp else None,
            "officer": {
                "id": officer.id if officer else None,
                "officer_name": officer.officer_name if officer else "",
                "nip": officer.nip if officer else "",
                "position": officer.position if officer else "",
                "institution": officer.institution if officer else "",
            } if officer else None,
            "start_date": m.start_date.isoformat() if m.start_date else None,
            "end_date": m.end_date.isoformat() if m.end_date else None,
            "description": m.description,
            "items": items,
        }
        self._save(db, transaction_type="maintenance", transaction_id=m.id,
                   snapshot_data=snapshot, archived_by=archived_by)


    # ── Read ──

    def get_snapshot(self, db: Session, transaction_type: str, transaction_id: int) -> dict | None:
        """Ambil snapshot terakhir untuk transaksi tertentu."""
        snap = (
            db.query(TransactionSnapshot)
            .filter(
                TransactionSnapshot.transaction_type == transaction_type,
                TransactionSnapshot.transaction_id == transaction_id,
            )
            .order_by(TransactionSnapshot.id.desc())
            .first()
        )
        if not snap:
            return None
        return {
            "id": snap.id,
            "transaction_type": snap.transaction_type,
            "transaction_id": snap.transaction_id,
            "snapshot_data": snap.snapshot_data,
            "completed_at": snap.completed_at.isoformat() if snap.completed_at else None,
        }
