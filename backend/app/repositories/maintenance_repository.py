from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.inventory_component import InventoryComponent
from app.models.inventory_item import InventoryItem
from app.models.maintenance import Maintenance
from app.models.maintenance_item import MaintenanceItem
from app.models.officer import Officer
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

    def get_filtered(
        self, db: Session, *,
        component_id=None, status=None,
        start_date=None, end_date=None,
        search: str | None = None,
        skip=0, limit=100, order_dir="desc",
        **kwargs,
    ) -> list[Maintenance]:
        order_col = Maintenance.id.asc() if order_dir == "asc" else Maintenance.id.desc()
        query = db.query(Maintenance)
        if component_id:
            query = query.filter(Maintenance.inventory_component_id == component_id)
        if status:
            query = query.filter(Maintenance.status == status)
        if start_date:
            query = query.filter(Maintenance.start_date >= start_date)
        if end_date:
            query = query.filter(Maintenance.start_date <= end_date)
        if search:
            search_term = search.strip()
            query = (
                query
                .outerjoin(InventoryComponent, Maintenance.inventory_component_id == InventoryComponent.id)
                .outerjoin(Officer, Maintenance.officer_id == Officer.id)
                .outerjoin(MaintenanceItem, Maintenance.id == MaintenanceItem.maintenance_id)
                .outerjoin(InventoryItem, MaintenanceItem.inventory_item_id == InventoryItem.id)
                .filter(
                    or_(
                        Maintenance.transaction_number.ilike(f"%{search_term}%"),
                        InventoryComponent.item_name.ilike(f"%{search_term}%"),
                        Officer.officer_name.ilike(f"%{search_term}%"),
                        InventoryItem.serial_number.ilike(f"%{search_term}%"),
                    )
                )
                .distinct()
            )
        return query.order_by(order_col).offset(skip).limit(limit).all()

    def count_filtered(
        self, db: Session, *,
        component_id=None, status=None,
        start_date=None, end_date=None,
        search: str | None = None,
    ) -> int:
        query = db.query(func.count(func.distinct(Maintenance.id)))
        if component_id:
            query = query.filter(Maintenance.inventory_component_id == component_id)
        if status:
            query = query.filter(Maintenance.status == status)
        if start_date:
            query = query.filter(Maintenance.start_date >= start_date)
        if end_date:
            query = query.filter(Maintenance.start_date <= end_date)
        if search:
            search_term = search.strip()
            query = (
                query
                .outerjoin(InventoryComponent, Maintenance.inventory_component_id == InventoryComponent.id)
                .outerjoin(Officer, Maintenance.officer_id == Officer.id)
                .outerjoin(MaintenanceItem, Maintenance.id == MaintenanceItem.maintenance_id)
                .outerjoin(InventoryItem, MaintenanceItem.inventory_item_id == InventoryItem.id)
                .filter(
                    or_(
                        Maintenance.transaction_number.ilike(f"%{search_term}%"),
                        InventoryComponent.item_name.ilike(f"%{search_term}%"),
                        Officer.officer_name.ilike(f"%{search_term}%"),
                        InventoryItem.serial_number.ilike(f"%{search_term}%"),
                    )
                )
            )
        return query.scalar() or 0
