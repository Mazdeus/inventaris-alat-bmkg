"""InventoryComponentRepository — query untuk tabel inventory_components."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.borrow_detail import BorrowDetail
from app.models.borrow_transaction import BorrowTransaction
from app.models.inventory_component import InventoryComponent
from app.repositories.base import BaseRepository


class InventoryComponentRepository(BaseRepository[InventoryComponent]):
    def __init__(self):
        super().__init__(InventoryComponent)

    def search_components(
        self, db: Session, *,
        search: str | None = None,
        status_id: int | None = None,
        procurement_year: int | None = None,
        division: str | None = None,
        skip: int = 0, limit: int = 100,
    ) -> list[InventoryComponent]:
        query = db.query(InventoryComponent)
        if search:
            query = query.filter(
                InventoryComponent.item_name.ilike(f"%{search}%") |
                InventoryComponent.brand.ilike(f"%{search}%") |
                InventoryComponent.serial_number.ilike(f"%{search}%")
            )
        if status_id is not None:
            query = query.filter(InventoryComponent.status_id == status_id)
        if procurement_year is not None:
            query = query.filter(InventoryComponent.procurement_year == procurement_year)
        if division is not None:
            query = query.filter(InventoryComponent.division == division)
        return query.order_by(InventoryComponent.id.desc()).offset(skip).limit(limit).all()

    def count_filtered(
        self, db: Session, *,
        search: str | None = None,
        status_id: int | None = None,
        procurement_year: int | None = None,
        division: str | None = None,
    ) -> int:
        query = db.query(func.count(InventoryComponent.id))
        if search:
            query = query.filter(
                InventoryComponent.item_name.ilike(f"%{search}%") |
                InventoryComponent.brand.ilike(f"%{search}%") |
                InventoryComponent.serial_number.ilike(f"%{search}%")
            )
        if status_id is not None:
            query = query.filter(InventoryComponent.status_id == status_id)
        if procurement_year is not None:
            query = query.filter(InventoryComponent.procurement_year == procurement_year)
        if division is not None:
            query = query.filter(InventoryComponent.division == division)
        return query.scalar() or 0

    def get_available_quantity(self, db: Session, component_id: int) -> int:
        """Hitung stok tersedia dari tabel inventory_items — status Available = status_id 1."""
        from app.models.inventory_item import InventoryItem
        return (
            db.query(func.count(InventoryItem.id))
            .filter(
                InventoryItem.inventory_component_id == component_id,
                InventoryItem.status_id == 1,  # Available
            )
            .scalar() or 0
        )

    def is_being_borrowed(self, db: Session, component_id: int) -> bool:
        """Cek apakah komponen sedang dipinjam (ada transaksi aktif)."""
        count = (
            db.query(func.count(BorrowDetail.id))
            .join(BorrowTransaction, BorrowDetail.borrow_id == BorrowTransaction.id)
            .filter(
                BorrowDetail.inventory_component_id == component_id,
                BorrowTransaction.status == "Dipinjam",
            )
            .scalar()
        )
        return (count or 0) > 0
