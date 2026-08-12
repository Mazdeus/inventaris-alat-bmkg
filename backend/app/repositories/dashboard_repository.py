"""DashboardRepository — query agregasi untuk dashboard."""
from datetime import date

from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.models.borrow_transaction import BorrowTransaction
from app.models.inventory_component import InventoryComponent


class DashboardRepository:
    def get_total_components(self, db: Session) -> int:
        return db.query(func.count(InventoryComponent.id)).scalar() or 0

    def get_total_items(self, db: Session) -> int:
        return db.query(func.sum(InventoryComponent.total_quantity)).scalar() or 0

    def get_status_summary(self, db: Session) -> dict:
        from app.models.inventory_status import InventoryStatus
        from app.models.inventory_item import InventoryItem
        results = (
            db.query(InventoryStatus.status_name, func.coalesce(func.count(InventoryItem.id), 0))
            .join(InventoryItem, InventoryStatus.id == InventoryItem.status_id, isouter=True)
            .group_by(InventoryStatus.id)
            .all()
        )
        return {name: int(count) for name, count in results}

    def get_active_borrows(self, db: Session) -> int:
        return (
            db.query(func.count(BorrowTransaction.id))
            .filter(BorrowTransaction.status == "Dipinjam")
            .scalar()
        ) or 0

    def get_pending_approvals(self, db: Session) -> int:
        return (
            db.query(func.count(BorrowTransaction.id))
            .filter(BorrowTransaction.status == "Menunggu")
            .scalar()
        ) or 0

    def get_overdue_returns(self, db: Session) -> int:
        return (
            db.query(func.count(BorrowTransaction.id))
            .filter(
                BorrowTransaction.status == "Dipinjam",
                BorrowTransaction.expected_return_date < date.today(),
            )
            .scalar()
        ) or 0

    def get_borrow_trend(self, db: Session, year: int) -> list[dict]:
        results = (
            db.query(
                extract("month", BorrowTransaction.borrow_date).label("month"),
                func.count(BorrowTransaction.id).label("total"),
            )
            .filter(extract("year", BorrowTransaction.borrow_date) == year)
            .group_by("month")
            .order_by("month")
            .all()
        )
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        data = {m: 0 for m in months}
        for row in results:
            idx = int(row.month) - 1
            if 0 <= idx < 12:
                data[months[idx]] = row.total
        return [{"month": m, "total": data[m]} for m in months]

    def get_procurement_by_year(self, db: Session) -> list[dict]:
        results = (
            db.query(
                InventoryComponent.procurement_year,
                func.sum(InventoryComponent.total_quantity).label("total"),
            )
            .filter(InventoryComponent.procurement_year.isnot(None))
            .group_by(InventoryComponent.procurement_year)
            .order_by(InventoryComponent.procurement_year)
            .all()
        )
        return [{"year": int(row[0]), "total": int(row[1])} for row in results]

    def get_procurement_by_month(self, db: Session, year: int) -> list[dict]:
        """Pengadaan per bulan untuk tahun tertentu (berdasarkan procurement_year)."""
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        total_in_year = (
            db.query(func.coalesce(func.sum(InventoryComponent.total_quantity), 0))
            .filter(InventoryComponent.procurement_year == year)
            .scalar()
        )
        # Sebar jumlah total ke semua bulan (representasi flat)
        avg = total_in_year // 12 if total_in_year else 0
        remainder = total_in_year % 12 if total_in_year else 0
        data = []
        for i, m in enumerate(months):
            data.append({"month": m, "total": avg + (1 if i < remainder else 0)})
        return data
