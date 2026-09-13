"""DashboardRepository — query agregasi untuk dashboard."""
from datetime import date

from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.models.borrow_transaction import BorrowTransaction
from app.models.inventory_component import InventoryComponent


class DashboardRepository:
    def get_total_components(self, db: Session, year: int | None = None) -> int:
        """Hitung seluruh jenis komponen aktif (tidak terhapus)."""
        q = db.query(func.count(InventoryComponent.id)).filter(InventoryComponent.deleted_at.is_(None))
        if year is not None:
            q = q.filter(InventoryComponent.procurement_year == year)
        return q.scalar() or 0

    def get_total_items(self, db: Session, year: int | None = None) -> int:
        """Hitung seluruh kuantitas fisik item dari komponen aktif."""
        q = db.query(func.coalesce(func.sum(InventoryComponent.total_quantity), 0)).filter(
            InventoryComponent.deleted_at.is_(None)
        )
        if year is not None:
            q = q.filter(InventoryComponent.procurement_year == year)
        return q.scalar() or 0

    def get_status_summary(self, db: Session) -> dict:
        """Hitung jumlah item fisik riil saat ini per status (Available, On Hold, Borrowed, dll)."""
        from app.models.inventory_status import InventoryStatus
        from app.models.inventory_item import InventoryItem

        query = (
            db.query(InventoryStatus.status_name, func.coalesce(func.count(InventoryItem.id), 0))
            .join(
                InventoryItem,
                (InventoryStatus.id == InventoryItem.status_id) & (
                    (InventoryStatus.status_name == "Deleted") | (InventoryItem.deleted_at.is_(None))
                ),
                isouter=True,
            )
            .join(
                InventoryComponent,
                (InventoryItem.inventory_component_id == InventoryComponent.id) & (
                    InventoryComponent.deleted_at.is_(None)
                ),
                isouter=True,
            )
            .group_by(InventoryStatus.id, InventoryStatus.status_name)
            .all()
        )
        return {name: int(count) for name, count in query}

    def get_active_borrows(self, db: Session) -> int:
        """Transaksi peminjaman yang saat ini sedang berlangsung (Borrowed)."""
        return db.query(func.count(BorrowTransaction.id)).filter(BorrowTransaction.status == "Borrowed").scalar() or 0

    def get_pending_approvals(self, db: Session) -> int:
        """Transaksi peminjaman yang saat ini masih menunggu persetujuan (Pending)."""
        return db.query(func.count(BorrowTransaction.id)).filter(BorrowTransaction.status == "Pending").scalar() or 0

    def get_overdue_returns(self, db: Session) -> int:
        """Transaksi peminjaman yang telah melewati perkiraan tanggal kembali."""
        return (
            db.query(func.count(BorrowTransaction.id))
            .filter(
                BorrowTransaction.status == "Borrowed",
                BorrowTransaction.expected_return_date < date.today(),
            )
            .scalar() or 0
        )

    # --- Aktivitas Berdasarkan Transaksi & Periode ---

    def get_handover_items_count(self, db: Session, year: int | None = None) -> int:
        """Hitung jumlah fisik barang yang diserahterimakan ke UPT berdasarkan tanggal pelimpahan."""
        from app.models.handover import Handover
        from app.models.handover_item import HandoverItem

        q = (
            db.query(func.count(HandoverItem.id))
            .join(Handover, HandoverItem.handover_id == Handover.id)
            .filter(Handover.status == "Transferred")
        )
        if year is not None:
            q = q.filter(extract("year", Handover.handover_date) == year)
        return q.scalar() or 0

    def get_borrow_count(self, db: Session, year: int | None = None) -> int:
        """Hitung total transaksi peminjaman pada periode tahun (berdasarkan borrow_date)."""
        q = db.query(func.count(BorrowTransaction.id))
        if year is not None:
            q = q.filter(extract("year", BorrowTransaction.borrow_date) == year)
        return q.scalar() or 0

    def get_maintenance_count(self, db: Session, year: int | None = None) -> int:
        """Hitung total pemeliharaan pada periode tahun (berdasarkan start_date)."""
        from app.models.maintenance import Maintenance

        q = db.query(func.count(Maintenance.id))
        if year is not None:
            q = q.filter(extract("year", Maintenance.start_date) == year)
        return q.scalar() or 0

    def get_procurement_count(self, db: Session, year: int | None = None) -> int:
        """Hitung total fisik barang yang diadakan pada periode tahun (berdasarkan procurement_year)."""
        q = db.query(func.coalesce(func.sum(InventoryComponent.total_quantity), 0)).filter(
            InventoryComponent.deleted_at.is_(None)
        )
        if year is not None:
            q = q.filter(InventoryComponent.procurement_year == year)
        return q.scalar() or 0

    def get_available_years(self, db: Session) -> list[int]:
        """Ambil daftar tahun unik yang ada data pengadaan atau transaksi."""
        from app.models.handover import Handover
        from app.models.maintenance import Maintenance

        years = set()
        current_year = date.today().year
        years.add(current_year)

        # Dari pengadaan
        p_years = (
            db.query(InventoryComponent.procurement_year)
            .filter(InventoryComponent.procurement_year.isnot(None), InventoryComponent.deleted_at.is_(None))
            .distinct()
            .all()
        )
        for (y,) in p_years:
            if y:
                years.add(int(y))

        # Dari peminjaman
        b_years = db.query(extract("year", BorrowTransaction.borrow_date)).distinct().all()
        for (y,) in b_years:
            if y:
                years.add(int(y))

        # Dari pelimpahan
        h_years = db.query(extract("year", Handover.handover_date)).distinct().all()
        for (y,) in h_years:
            if y:
                years.add(int(y))

        # Dari pemeliharaan
        m_years = db.query(extract("year", Maintenance.start_date)).distinct().all()
        for (y,) in m_years:
            if y:
                years.add(int(y))

        return sorted(list(years), reverse=True)

    def get_borrow_trend(self, db: Session, year: int | None = None) -> list[dict]:
        """Tren peminjaman per bulan (12 bulan Jan - Des). Difilter tahun jika diberikan."""
        months = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
                  "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
        q = (
            db.query(
                extract("month", BorrowTransaction.borrow_date).label("month"),
                func.count(BorrowTransaction.id).label("total"),
            )
        )
        if year is not None:
            q = q.filter(extract("year", BorrowTransaction.borrow_date) == year)
        results = q.group_by("month").order_by("month").all()

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
            .filter(
                InventoryComponent.procurement_year.isnot(None),
                InventoryComponent.deleted_at.is_(None),
            )
            .group_by(InventoryComponent.procurement_year)
            .order_by(InventoryComponent.procurement_year)
            .all()
        )
        return [{"year": int(row[0]), "total": int(row[1])} for row in results]

    def get_procurement_by_month(self, db: Session, year: int | None = None) -> list[dict]:
        """Pengadaan per bulan (12 bulan Jan - Des). Difilter tahun jika diberikan."""
        months = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
                  "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
        q = (
            db.query(
                InventoryComponent.procurement_month,
                func.sum(InventoryComponent.total_quantity).label("total"),
            )
            .filter(InventoryComponent.deleted_at.is_(None))
        )
        if year is not None:
            q = q.filter(InventoryComponent.procurement_year == year)
        results = q.group_by(InventoryComponent.procurement_month).all()

        data = {i + 1: 0 for i in range(12)}
        for row in results:
            m = int(row[0]) if row[0] else 0
            if 1 <= m <= 12:
                data[m] = int(row[1] or 0)
        return [{"month": months[i], "total": data[i + 1]} for i in range(12)]
