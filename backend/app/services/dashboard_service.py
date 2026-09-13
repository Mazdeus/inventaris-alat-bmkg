"""DashboardService — agregasi data untuk dashboard."""
from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import DashboardRepository


class DashboardService:
    def __init__(self):
        self.repo = DashboardRepository()

    def get_summary(self, db: Session, year: int | None = None) -> dict:
        status = self.repo.get_status_summary(db)
        status_dict = {
            "available": status.get("Available", 0),
            "on_hold": status.get("On Hold", 0),
            "borrowed": status.get("Borrowed", 0),
            "maintenance": status.get("Maintenance", 0),
            "broken": status.get("Broken", 0),
            "deleted": status.get("Deleted", 0),
            "transferred": status.get("Transferred", 0),
        }
        total_components = int(self.repo.get_total_components(db))
        total_items = int(self.repo.get_total_items(db))
        active_borrows = int(self.repo.get_active_borrows(db))
        pending_approvals = int(self.repo.get_pending_approvals(db))
        overdue_returns = int(self.repo.get_overdue_returns(db))

        # Aktivitas transaksi pada periode tahun yang dipilih (atau all-time jika year is None)
        period_activity = {
            "year": year,
            "handovers": int(self.repo.get_handover_items_count(db, year)),
            "borrows": int(self.repo.get_borrow_count(db, year)),
            "maintenances": int(self.repo.get_maintenance_count(db, year)),
            "procurements": int(self.repo.get_procurement_count(db, year)),
        }

        available_years = self.repo.get_available_years(db)

        return {
            # Real-time physical stock metrics
            "total_components": total_components,
            "total_items": total_items,
            "status_summary": status_dict,
            "active_borrows": active_borrows,
            "pending_approvals": pending_approvals,
            "overdue_returns": overdue_returns,
            # Period activity metrics
            "period_activity": period_activity,
            "available_years": available_years,
        }

    def get_charts(self, db: Session, year: int | None = None) -> dict:
        status = self.repo.get_status_summary(db)
        return {
            "target_year": year,
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
