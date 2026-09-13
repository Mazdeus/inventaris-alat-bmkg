"""MaintenanceService — logika bisnis riwayat pemeliharaan. (UR-08, FR-26)"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.inventory_component import InventoryComponent
from app.models.inventory_item import InventoryItem
from app.models.inventory_status import InventoryStatus
from app.models.maintenance import Maintenance
from app.models.maintenance_item import MaintenanceItem
from app.models.officer import Officer
from app.models.user import User
from app.repositories.maintenance_repository import MaintenanceRepository
from app.schemas.maintenance import (
    ComponentBrief,
    MaintenanceCreate,
    MaintenanceItemResponse,
    MaintenanceOfficerBrief,
    MaintenanceResponse,
    MaintenanceUpdate,
)
from app.services.activity_log_service import ActivityLogService
from app.services.inventory_service import InventoryService
from app.services.transaction_number_service import generate_transaction_number
from app.services.transaction_snapshot_service import TransactionSnapshotService
from app.core.logging_config import get_logger

logger = get_logger()

inv_svc = InventoryService()  # instance untuk shared _write_history

# Status yang boleh dimasukkan ke pemeliharaan (hanya barang di gudang)
ALLOWED_PREVIOUS_STATUSES = ["Available", "Broken"]


class MaintenanceService:
    def __init__(self):
        self.repo = MaintenanceRepository()
        self.log_svc = ActivityLogService()
        self.snapshot_svc = TransactionSnapshotService()

    def _find_status_id(self, db: Session, name: str) -> int:
        s = db.query(InventoryStatus).filter(InventoryStatus.status_name == name).first()
        return s.id if s else 1

    def _find_status_name(self, db: Session, status_id: int) -> str:
        if not status_id:
            return ""
        s = db.query(InventoryStatus).filter(InventoryStatus.id == status_id).first()
        return s.status_name if s else ""

    def _to_response(self, m: Maintenance, snapshot_data: dict | None = None) -> MaintenanceResponse:
        comp = m.inventory_component
        if snapshot_data:
            c_data = snapshot_data.get("component")
            comp_obj = ComponentBrief(
                id=c_data.get("id") or 0,
                item_name=c_data.get("item_name") or "",
                brand=c_data.get("brand"),
                model=c_data.get("model"),
                serial_number=c_data.get("serial_number"),
                total_quantity=c_data.get("total_quantity") or 0,
                status=c_data.get("status") or "",
            ) if c_data else None

            o_data = snapshot_data.get("officer")
            officer_obj = MaintenanceOfficerBrief(
                id=o_data.get("id") or 0,
                officer_name=o_data.get("officer_name") or o_data.get("name") or "",
            ) if o_data else None

            if "items" in snapshot_data and snapshot_data["items"]:
                item_responses = [
                    MaintenanceItemResponse(
                        id=it.get("id") or 0,
                        inventory_item_id=it.get("inventory_item_id") or 0,
                        serial_number=it.get("serial_number"),
                        previous_status=it.get("previous_status") or "",
                    )
                    for it in snapshot_data["items"]
                ]
            else:
                item_responses = []
                if m.maintenance_items:
                    for mi in m.maintenance_items:
                        it = mi.inventory_item
                        sn = it.serial_number if it else None
                        prev = self._find_status_name_for_mi(mi)
                        item_responses.append(MaintenanceItemResponse(
                            id=mi.id,
                            inventory_item_id=mi.inventory_item_id,
                            serial_number=sn,
                            previous_status=prev,
                        ))
        else:
            item_responses = []
            if m.maintenance_items:
                for mi in m.maintenance_items:
                    it = mi.inventory_item
                    sn = it.serial_number if it else None
                    prev = self._find_status_name_for_mi(mi)
                    item_responses.append(MaintenanceItemResponse(
                        id=mi.id,
                        inventory_item_id=mi.inventory_item_id,
                        serial_number=sn,
                        previous_status=prev,
                    ))

            comp_obj = ComponentBrief(
                id=comp.id, item_name=comp.item_name,
                serial_number=", ".join(
                    [r.serial_number for r in item_responses if r.serial_number]
                ) or None,
                status=comp.status.status_name if comp.status else "",
            ) if comp else None

            officer_obj = MaintenanceOfficerBrief(
                id=m.officer.id, officer_name=m.officer.officer_name,
            ) if m.officer else None

        return MaintenanceResponse(
            id=m.id,
            transaction_number=m.transaction_number,
            daily_sequence=m.daily_sequence,
            component=comp_obj,
            officer=officer_obj,
            start_date=m.start_date,
            end_date=m.end_date,
            description=m.description,
            status=m.status,
            component_status=comp.status.status_name if comp and comp.status else None,
            items=item_responses,
        )

    def _find_status_name_for_mi(self, mi: MaintenanceItem) -> str:
        """Ambil nama status sebelumnya dari MaintenanceItem."""
        if mi.previous_status:
            return mi.previous_status.status_name
        return ""

    def get_maintenances(self, db: Session, *, page=1, size=10, component_id=None, status=None, start_date=None, end_date=None, order_dir="desc"):
        skip = (page - 1) * size
        items = self.repo.get_filtered(
            db, component_id=component_id, status=status,
            start_date=start_date, end_date=end_date,
            skip=skip, limit=size, order_dir=order_dir,
        )
        total = self.repo.count_filtered(
            db, component_id=component_id, status=status,
            start_date=start_date, end_date=end_date,
        )
        if not items:
            return [], total

        from app.models.transaction_snapshot import TransactionSnapshot
        snapshots = (
            db.query(TransactionSnapshot)
            .filter(
                TransactionSnapshot.transaction_type == "maintenance",
                TransactionSnapshot.transaction_id.in_([m.id for m in items]),
            )
            .all()
        )
        snap_map = {s.transaction_id: s.snapshot_data for s in snapshots if s.snapshot_data}
        return [self._to_response(m, snapshot_data=snap_map.get(m.id)) for m in items], total

    def get_maintenance_detail(self, db: Session, maint_id: int) -> MaintenanceResponse:
        m = self.repo.get(db, maint_id)
        if not m:
            raise HTTPException(status_code=404, detail="Data pemeliharaan tidak ditemukan")
        snap = self.snapshot_svc.get_snapshot(db, "maintenance", m.id)
        snapshot_data = snap.get("snapshot_data") if snap else None
        return self._to_response(m, snapshot_data=snapshot_data)


    def create_maintenance(self, db: Session, data: MaintenanceCreate, current_user: User) -> MaintenanceResponse:
        comp = db.query(InventoryComponent).filter(InventoryComponent.id == data.inventory_component_id).first()
        if not comp:
            raise HTTPException(status_code=404, detail="Unit tidak ditemukan")

        # Validasi petugas pemeliharaan
        officer = db.query(Officer).filter(Officer.id == data.officer_id).first()
        if not officer:
            raise HTTPException(status_code=404, detail="Petugas pemeliharaan tidak ditemukan")

        # Validasi item_ids: hanya barang Available atau Broken yang boleh dirawat
        if not data.item_ids:
            raise HTTPException(status_code=400, detail="Minimal pilih 1 barang untuk pemeliharaan")

        items = db.query(InventoryItem).filter(InventoryItem.id.in_(data.item_ids)).all()
        if not items:
            raise HTTPException(status_code=400, detail="Barang yang dipilih tidak ditemukan")

        maint_status_id = self._find_status_id(db, "Maintenance")
        available_id = self._find_status_id(db, "Available")
        broken_id = self._find_status_id(db, "Broken")

        for item in items:
            if item.status_id not in (available_id, broken_id):
                status_name = item.status.status_name if item.status else str(item.status_id)
                raise HTTPException(
                    status_code=400,
                    detail=f"Barang SN '{item.serial_number or '#'+str(item.id)}' "
                           f"berstatus '{status_name}'. Hanya barang Tersedia atau Rusak yang bisa dirawat.",
                )

        # Validasi: status Selesai (Completed) wajib mengisi Tanggal Selesai
        if data.status == "Completed" and not data.end_date:
            raise HTTPException(
                status_code=422,
                detail="Tanggal Selesai wajib diisi saat status Selesai.",
            )

        # Simpan record Maintenance dengan nomor transaksi
        m_number, m_seq = generate_transaction_number(db, "maintenance")
        m_data = data.model_dump(exclude={"item_ids"})
        m_data["transaction_number"] = m_number
        m_data["daily_sequence"] = m_seq
        m = Maintenance(**m_data)
        db.add(m)
        db.flush()  # Dapatkan m.id

        # Simpan MaintenanceItem untuk setiap item
        inv_svc = InventoryService()
        for item in items:
            mi = MaintenanceItem(
                maintenance_id=m.id,
                inventory_item_id=item.id,
                previous_status_id=item.status_id,
            )
            db.add(mi)
            # Ubah status item: status Selesai → langsung kembali Tersedia; selain itu → Perbaikan
            old_status_id = item.status_id
            item.status_id = available_id if data.status == "Completed" else maint_status_id
            # Catat riwayat
            inv_svc._write_history(db,
                item_id=item.id, component_id=item.inventory_component_id,
                from_status_id=old_status_id, to_status_id=item.status_id,
                source="MAINTENANCE", maintenance_id=m.id, user_id=current_user.id,
                notes=f"Pemeliharaan #{m.id} ({m.description or 'Mulai pemeliharaan'})",
            )

        db.commit()
        db.refresh(m)

        # Recompute status komponen dari items
        inv_svc.recompute_component_status(db, comp.id)

        logger.info("Pemeliharaan komponen '%s' dicatat oleh %s", comp.item_name, current_user.full_name)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} mencatat pemeliharaan komponen '{comp.item_name}'",
                         reference_table="maintenance", reference_id=m.id,
                         reference_path="/maintenance")

        return self._to_response(m)

    def update_maintenance(self, db: Session, maint_id: int, data: MaintenanceUpdate, current_user: User) -> MaintenanceResponse:
        m = self.repo.get(db, maint_id)
        if not m:
            raise HTTPException(status_code=404, detail="Data pemeliharaan tidak ditemukan")

        if m.status != "In Progress":
            raise HTTPException(
                status_code=409,
                detail=f"Pemeliharaan dengan status '{m.status}' tidak bisa diedit. "
                       f"Hanya pemeliharaan Dalam Proses yang bisa diedit.",
            )

        update_data = data.model_dump(exclude_unset=True)

        # Validasi: status Selesai (Completed) wajib mengisi Tanggal Selesai
        if data.status == "Completed":
            has_end_date = data.end_date is not None or m.end_date is not None
            if not has_end_date:
                raise HTTPException(
                    status_code=422,
                    detail="Tanggal Selesai wajib diisi saat status diubah menjadi Selesai.",
                )

        for k, v in update_data.items():
            setattr(m, k, v)

        comp = m.inventory_component
        inv_svc = InventoryService()

        # Jika Completed → kembalikan item ke Available (end_date sudah tervalidasi)
        if data.status == "Completed" and comp:
            available_id = self._find_status_id(db, "Available")
            for mi in m.maintenance_items:
                item = db.query(InventoryItem).filter(InventoryItem.id == mi.inventory_item_id).first()
                if item:
                    old_status_id = item.status_id
                    item.status_id = available_id
                    inv_svc._write_history(db,
                        item_id=item.id, component_id=item.inventory_component_id,
                        from_status_id=old_status_id, to_status_id=available_id,
                        source="MAINTENANCE", maintenance_id=m.id, user_id=current_user.id,
                        notes=f"Pemeliharaan #{m.id} selesai ({m.description or 'Selesai'})",
                    )
            inv_svc.recompute_component_status(db, comp.id)

        # Jika Cancelled → kembalikan item ke status sebelum pemeliharaan
        elif data.status == "Cancelled" and comp:
            for mi in m.maintenance_items:
                if mi.previous_status_id:
                    item = db.query(InventoryItem).filter(InventoryItem.id == mi.inventory_item_id).first()
                    if item:
                        old_status_id = item.status_id
                        item.status_id = mi.previous_status_id
                        inv_svc._write_history(db,
                            item_id=item.id, component_id=item.inventory_component_id,
                            from_status_id=old_status_id, to_status_id=mi.previous_status_id,
                            source="MAINTENANCE", maintenance_id=m.id, user_id=current_user.id,
                            notes=f"Pemeliharaan #{m.id} dibatalkan",
                        )
            inv_svc.recompute_component_status(db, comp.id)

        # Simpan snapshot saat pemeliharaan selesai/dibatalkan
        if data.status in ("Completed", "Cancelled"):
            self.snapshot_svc.create_maintenance_snapshot(db, m, archived_by=current_user.id)


        db.commit()
        db.refresh(m)

        logger.info("Pemeliharaan #%s diperbarui menjadi '%s' oleh %s", maint_id, m.status, current_user.full_name)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} memperbarui pemeliharaan #{maint_id}",
                         reference_table="maintenance", reference_id=m.id,
                         reference_path="/maintenance")

        return self._to_response(m)

    # Catatan: fitur hapus pemeliharaan dihapus karena tidak ada status yang boleh dihapus
    # (Dalam Proses tidak bisa dihapus, Selesai & Dibatalkan final, Terjadwal sudah dihapus).
