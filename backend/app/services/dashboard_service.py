"""DashboardService — agregasi data untuk dashboard."""
from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import DashboardRepository


class DashboardService:
    def __init__(self):
        self.repo = DashboardRepository()

    def get_summary(self, db: Session, year: int | None = None) -> dict:
        status = self.repo.get_status_summary(db, year)
        return {
            "total_components": self.repo.get_total_components(db, year),
            "total_items": self.repo.get_total_items(db, year),
            "status_summary": {
                "available": status.get("Available", 0),
                "on_hold": status.get("On Hold", 0),
                "borrowed": status.get("Borrowed", 0),
                "maintenance": status.get("Maintenance", 0),
                "broken": status.get("Broken", 0),
                "deleted": status.get("Deleted", 0),
                "transferred": status.get("Transferred", 0),
            },
            "active_borrows": self.repo.get_active_borrows(db, year),
            "pending_approvals": self.repo.get_pending_approvals(db, year),
            "overdue_returns": self.repo.get_overdue_returns(db, year),
        }

    def get_charts(self, db: Session, year: int | None = None) -> dict:
        if year is None:
            from datetime import date
            year = date.today().year

        status = self.repo.get_status_summary(db)
        return {
            "borrow_trend": self.repo.get_borrow_trend(db, year),
            "status_distribution": {
                "labels": ["Tersedia", "Ditahan", "Dipinjam", "Perbaikan", "Rusak", "Dihapuskan", "Dilimpahkan"],
                "values": [
                    status.get("Available", 0),
                    status.get("On Hold", 0),
                    status.get("Borrowed", 0),
                    status.get("Maintenance", 0),
                    status.get("Broken", 0),
                    status.get("Deleted", 0),
                    status.get("Transferred", 0),
                ],
            },
            "procurement_by_year": self.repo.get_procurement_by_year(db),
            "procurement_by_month": self.repo.get_procurement_by_month(db, year),
        }
