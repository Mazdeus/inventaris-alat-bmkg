"""MaintenanceService — logika bisnis riwayat perbaikan. (UR-08, FR-26)"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.inventory_component import InventoryComponent
from app.models.inventory_item import InventoryItem
from app.models.inventory_status import InventoryStatus
from app.models.maintenance import Maintenance
from app.models.user import User
from app.repositories.maintenance_repository import MaintenanceRepository
from app.schemas.maintenance import ComponentBrief, MaintenanceCreate, MaintenanceResponse, MaintenanceUpdate
from app.services.activity_log_service import ActivityLogService
from app.services.inventory_service import InventoryService


class MaintenanceService:
    def __init__(self):
        self.repo = MaintenanceRepository()
        self.log_svc = ActivityLogService()

    def _find_status_id(self, db: Session, name: str) -> int:
        s = db.query(InventoryStatus).filter(InventoryStatus.status_name == name).first()
        return s.id if s else 1

    def _to_response(self, m: Maintenance) -> MaintenanceResponse:
        comp = m.inventory_component
        # Ambil SN dari item-item yang sedang Maintenance untuk komponen ini
        item_sns = self._get_maintenance_item_sns(m) if comp else []
        return MaintenanceResponse(
            id=m.id,
            component=ComponentBrief(
                id=comp.id, item_name=comp.item_name,
                serial_number=", ".join(item_sns) if item_sns else None,
                status=comp.status.status_name if comp.status else "",
            ) if comp else None,
            start_date=m.start_date,
            end_date=m.end_date,
            description=m.description,
            status=m.status,
            component_status=comp.status.status_name if comp and comp.status else None,
        )

    def _get_maintenance_item_sns(self, m: Maintenance) -> list:
        """Ambil serial number item yang sedang Maintenance untuk komponen maintenance ini."""
        from app.models.inventory_item import InventoryItem
        from sqlalchemy.orm import Session as _Session
        # Butuh db session — query dari object session
        if hasattr(m, '_sa_instance_state'):
            sess = _Session.object_session(m)
            if sess:
                maint_status_id = self._find_status_id(sess, "Maintenance")
                items = sess.query(InventoryItem).filter(
                    InventoryItem.inventory_component_id == m.inventory_component_id,
                    InventoryItem.status_id == maint_status_id,
                ).all()
                return [it.serial_number for it in items if it.serial_number]
        return []

    def get_maintenances(self, db: Session, *, page=1, size=10, component_id=None, status=None):
        skip = (page - 1) * size
        items = self.repo.get_filtered(db, component_id=component_id, status=status, skip=skip, limit=size)
        total = self.repo.count(db)
        return [self._to_response(m) for m in items], total

    def get_maintenance_detail(self, db: Session, maint_id: int) -> MaintenanceResponse:
        m = self.repo.get(db, maint_id)
        if not m:
            raise HTTPException(status_code=404, detail="Data maintenance tidak ditemukan")
        return self._to_response(m)

    def create_maintenance(self, db: Session, data: MaintenanceCreate, current_user: User) -> MaintenanceResponse:
        comp = db.query(InventoryComponent).filter(InventoryComponent.id == data.inventory_component_id).first()
        if not comp:
            raise HTTPException(status_code=404, detail="Unit tidak ditemukan")

        m = Maintenance(**data.model_dump(exclude={"item_ids"}))
        db.add(m)

        # Update item yang dipilih menjadi "Maintenance"
        maint_id = self._find_status_id(db, "Maintenance")
        if data.item_ids:
            items = db.query(InventoryItem).filter(InventoryItem.id.in_(data.item_ids)).all()
            for item in items:
                item.status_id = maint_id
        else:
            # Jika tidak ada item_ids, update semua item Broken → Maintenance
            broken_items = db.query(InventoryItem).filter(
                InventoryItem.inventory_component_id == data.inventory_component_id,
                InventoryItem.status_id == self._find_status_id(db, "Broken"),
            ).all()
            for item in broken_items:
                item.status_id = maint_id

        # Update status komponen
        comp.status_id = maint_id
        db.commit()
        db.refresh(m)

        # Recompute status komponen dari items
        InventoryService().recompute_component_status(db, comp.id)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} mencatat maintenance komponen '{comp.item_name}'",
                         reference_table="maintenance", reference_id=m.id)

        return self._to_response(m)

    def update_maintenance(self, db: Session, maint_id: int, data: MaintenanceUpdate, current_user: User) -> MaintenanceResponse:
        m = self.repo.get(db, maint_id)
        if not m:
            raise HTTPException(status_code=404, detail="Data maintenance tidak ditemukan")

        update_data = data.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(m, k, v)

        # Jika completed + end_date → kembalikan item ke Available
        if data.status == "Completed" and data.end_date:
            comp = m.inventory_component
            if comp:
                available_id = self._find_status_id(db, "Available")
                # Update item yang statusnya Maintenance → Available
                items = db.query(InventoryItem).filter(
                    InventoryItem.inventory_component_id == comp.id,
                    InventoryItem.status_id == self._find_status_id(db, "Maintenance"),
                ).all()
                for item in items:
                    item.status_id = available_id
                InventoryService().recompute_component_status(db, comp.id)

        db.commit()
        db.refresh(m)

        self.log_svc.log(db, user_id=current_user.id,
                         activity=f"{current_user.full_name} memperbarui maintenance #{maint_id}",
                         reference_table="maintenance", reference_id=m.id)

        return self._to_response(m)
