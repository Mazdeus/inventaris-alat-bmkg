"""MaintenanceService — logika bisnis riwayat perawatan. (UR-08, FR-26)"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.inventory_component import InventoryComponent
from app.models.inventory_item import InventoryItem
from app.models.inventory_status import InventoryStatus
from app.models.maintenance import Maintenance
from app.models.maintenance_item import MaintenanceItem
from app.models.user import User
from app.repositories.maintenance_repository import MaintenanceRepository
from app.schemas.maintenance import (
    ComponentBrief,
    MaintenanceCreate,
    MaintenanceItemResponse,
    MaintenanceResponse,
    MaintenanceUpdate,
)
from app.services.activity_log_service import ActivityLogService
from app.services.inventory_service import InventoryService

# Status yang boleh dimasukkan ke perawatan (hanya barang di gudang)
ALLOWED_PREVIOUS_STATUSES = ["Available", "Broken"]


class MaintenanceService:
    def __init__(self):
        self.repo = MaintenanceRepository()
        self.log_svc = ActivityLogService()

    def _find_status_id(self, db: Session, name: str) -> int:
        s = db.query(InventoryStatus).filter(InventoryStatus.status_name == name).first()
        return s.id if s else 1

    def _find_status_name(self, db: Session, status_id: int) -> str:
        if not status_id:
            return ""
        s = db.query(InventoryStatus).filter(InventoryStatus.id == status_id).first()
        return s.status_name if s else ""

    def _to_response(self, m: Maintenance) -> MaintenanceResponse:
        comp = m.inventory_component
        # Ambil daftar item dari maintenance_items yang tercatat
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

        return MaintenanceResponse(
            id=m.id,
            component=ComponentBrief(
                id=comp.id, item_name=comp.item_name,
                serial_number=", ".join(
                    [r.serial_number for r in item_responses if r.serial_number]
                ) or None,
                status=comp.status.status_name if comp.status else "",
            ) if comp else None,
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

    def get_maintenances(self, db: Session, *, page=1, size=10, component_id=None, status=None):
        skip = (page - 1) * size
        items = self.repo.get_filtered(db, component_id=component_id, status=status, skip=skip, limit=size)
        total = self.repo.count(db)
        return [self._to_response(m) for m in items], total

    def get_maintenance_detail(self, db: Session, maint_id: int) -> MaintenanceResponse:
        m = self.repo.get(db, maint_id)
        if not m:
            raise HTTPException(status_code=404, detail="Data perawatan tidak ditemukan")
        return self._to_response(m)

    def create_maintenance(self, db: Session, data: MaintenanceCreate, current_user: User) -> MaintenanceResponse:
        comp = db.query(InventoryComponent).filter(InventoryComponent.id == data.inventory_component_id).first()
        if not comp:
            raise HTTPException(status_code=404, detail="Unit tidak ditemukan")

        # Validasi item_ids: hanya barang Available atau Broken yang boleh dirawat
        if not data.item_ids:
            raise HTTPException(status_code=400, detail="Minimal pilih 1 barang untuk perawatan")

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

        # Simpan record Maintenance (tanpa item_ids — itu bukan kolom)
        m = Maintenance(**data.model_dump(exclude={"item_ids"}))
        db.add(m)
        db.flush()  # Dapatkan m.id

        # Simpan MaintenanceItem untuk setiap item
        for item in items:
            mi = MaintenanceItem(
                maintenance_id=m.id,
                inventory_item_id=item.id,
                previous_status_id=item.status_id,
            )
            db.add(mi)
            # Ubah status item menjadi Maintenance
            item.status_id = maint_status_id

        db.commit()
        db.refresh(m)

        # Recompute status komponen dari items
        InventoryService().recompute_component_status(db, comp.id)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} mencatat perawatan komponen '{comp.item_name}'",
                         reference_table="maintenance", reference_id=m.id)

        return self._to_response(m)

    def update_maintenance(self, db: Session, maint_id: int, data: MaintenanceUpdate, current_user: User) -> MaintenanceResponse:
        m = self.repo.get(db, maint_id)
        if not m:
            raise HTTPException(status_code=404, detail="Data perawatan tidak ditemukan")

        update_data = data.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(m, k, v)

        comp = m.inventory_component

        # Jika Completed + end_date → kembalikan item ke Available
        if data.status == "Completed" and data.end_date and comp:
            available_id = self._find_status_id(db, "Available")
            for mi in m.maintenance_items:
                item = db.query(InventoryItem).filter(InventoryItem.id == mi.inventory_item_id).first()
                if item:
                    item.status_id = available_id
            InventoryService().recompute_component_status(db, comp.id)

        # Jika Cancelled → kembalikan item ke status sebelum perawatan
        elif data.status == "Cancelled" and comp:
            for mi in m.maintenance_items:
                if mi.previous_status_id:
                    item = db.query(InventoryItem).filter(InventoryItem.id == mi.inventory_item_id).first()
                    if item:
                        item.status_id = mi.previous_status_id
            InventoryService().recompute_component_status(db, comp.id)

        db.commit()
        db.refresh(m)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} memperbarui perawatan #{maint_id}",
                         reference_table="maintenance", reference_id=m.id)

        return self._to_response(m)
