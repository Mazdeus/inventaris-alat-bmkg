"""MaintenanceRepository — query untuk tabel maintenance."""
from sqlalchemy.orm import Session

from app.models.maintenance import Maintenance
from app.repositories.base import BaseRepository


class MaintenanceRepository(BaseRepository[Maintenance]):
    def __init__(self):
        super().__init__(Maintenance)

    def get_by_component(self, db: Session, component_id: int, *, skip=0, limit=100) -> list[Maintenance]:
        return (
            db.query(Maintenance)
            .filter(Maintenance.inventory_component_id == component_id)
            .order_by(Maintenance.id.desc())
            .offset(skip).limit(limit).all()
        )

    def get_filtered(self, db: Session, *, component_id=None, status=None, skip=0, limit=100) -> list[Maintenance]:
        query = db.query(Maintenance).order_by(Maintenance.id.desc())
        if component_id:
            query = query.filter(Maintenance.inventory_component_id == component_id)
        if status:
            query = query.filter(Maintenance.status == status)
        return query.offset(skip).limit(limit).all()
