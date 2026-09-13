from sqlalchemy import func
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

    def get_filtered(self, db: Session, *, component_id=None, status=None, start_date=None, end_date=None, skip=0, limit=100, order_dir="desc", **kwargs) -> list[Maintenance]:
        order_col = Maintenance.id.asc() if order_dir == "asc" else Maintenance.id.desc()
        query = db.query(Maintenance).order_by(order_col)
        if component_id:
            query = query.filter(Maintenance.inventory_component_id == component_id)
        if status:
            query = query.filter(Maintenance.status == status)
        if start_date:
            query = query.filter(Maintenance.start_date >= start_date)
        if end_date:
            query = query.filter(Maintenance.start_date <= end_date)
        return query.offset(skip).limit(limit).all()

    def count_filtered(self, db: Session, *, component_id=None, status=None, start_date=None, end_date=None) -> int:
        query = db.query(func.count(Maintenance.id))
        if component_id:
            query = query.filter(Maintenance.inventory_component_id == component_id)
        if status:
            query = query.filter(Maintenance.status == status)
        if start_date:
            query = query.filter(Maintenance.start_date >= start_date)
        if end_date:
            query = query.filter(Maintenance.start_date <= end_date)
        return query.scalar() or 0
