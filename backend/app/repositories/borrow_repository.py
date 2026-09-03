"""BorrowRepository — query untuk tabel borrow_transactions."""
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.borrow_detail import BorrowDetail
from app.models.borrow_detail_item import BorrowDetailItem
from app.models.borrow_transaction import BorrowTransaction
from app.repositories.base import BaseRepository


class BorrowRepository(BaseRepository[BorrowTransaction]):
    def __init__(self):
        super().__init__(BorrowTransaction)

    def get_with_details(self, db: Session, transaction_id: int) -> BorrowTransaction | None:
        return (
            db.query(BorrowTransaction)
            .options(
                joinedload(BorrowTransaction.borrower),
                joinedload(BorrowTransaction.officer),
                joinedload(BorrowTransaction.borrow_details)
                .joinedload(BorrowDetail.inventory_component),
                joinedload(BorrowTransaction.borrow_details)
                .joinedload(BorrowDetail.borrow_detail_items)
                .joinedload(BorrowDetailItem.inventory_item),
            )
            .filter(BorrowTransaction.id == transaction_id)
            .first()
        )

    def get_filtered(
        self, db: Session, *,
        start_date=None, end_date=None,
        borrower_name: str | None = None,
        status: str | None = None,
        skip: int = 0, limit: int = 100,
    ) -> list[BorrowTransaction]:
        query = (
            db.query(BorrowTransaction)
            .options(
                joinedload(BorrowTransaction.borrower),
                joinedload(BorrowTransaction.officer),
                joinedload(BorrowTransaction.borrow_details),
            )
            .order_by(BorrowTransaction.id.desc())
        )

        if start_date:
            query = query.filter(BorrowTransaction.borrow_date >= start_date)
        if end_date:
            query = query.filter(BorrowTransaction.borrow_date <= end_date)
        if borrower_name:
            query = query.join(BorrowTransaction.borrower).filter(
                BorrowTransaction.borrower.has(borrower_name__ilike=f"%{borrower_name}%")
            )
        if status:
            query = query.filter(BorrowTransaction.status == status)

        return query.offset(skip).limit(limit).all()

    def count_filtered(
        self, db: Session, *,
        start_date=None, end_date=None,
        borrower_name: str | None = None,
        status: str | None = None,
    ) -> int:
        query = db.query(func.count(BorrowTransaction.id))
        if start_date:
            query = query.filter(BorrowTransaction.borrow_date >= start_date)
        if end_date:
            query = query.filter(BorrowTransaction.borrow_date <= end_date)
        if borrower_name:
            from app.models.borrower import Borrower
            query = query.join(Borrower, BorrowTransaction.borrower_id == Borrower.id).filter(
                Borrower.borrower_name.ilike(f"%{borrower_name}%")
            )
        if status:
            query = query.filter(BorrowTransaction.status == status)
        return query.scalar() or 0

    def count_borrowed_quantity(self, db: Session, component_id: int) -> int:
        """Total quantity yang sedang dipinjam aktif untuk satu komponen."""
        from app.models.borrow_detail import BorrowDetail as BD
        result = (
            db.query(func.coalesce(func.sum(BD.quantity), 0))
            .join(BorrowTransaction, BD.borrow_id == BorrowTransaction.id)
            .filter(
                BD.inventory_component_id == component_id,
                BorrowTransaction.status == "Borrowed",
            )
            .scalar()
        )
        return result or 0

    def get_by_ids(self, db: Session, ids: list[int]) -> list[BorrowTransaction]:
        """Ambil transaksi berdasarkan daftar ID."""
        return db.query(BorrowTransaction).filter(BorrowTransaction.id.in_(ids)).all()

    def delete_borrow_detail_items_by_transaction_ids(self, db: Session, ids: list[int]) -> int:
        """Hapus semua borrow_detail_items untuk daftar ID transaksi."""
        from app.models.borrow_detail import BorrowDetail as BD
        item_ids = [
            row[0] for row in (
                db.query(BorrowDetailItem.id)
                .join(BD, BorrowDetailItem.borrow_detail_id == BD.id)
                .filter(BD.borrow_id.in_(ids))
                .all()
            )
        ]
        if not item_ids:
            return 0
        deleted = (
            db.query(BorrowDetailItem)
            .filter(BorrowDetailItem.id.in_(item_ids))
            .delete(synchronize_session=False)
        )
        return deleted

    def delete_details_by_transaction_ids(self, db: Session, ids: list[int]) -> int:
        """Hapus semua borrow_details untuk daftar ID transaksi. Kembalikan jumlah yang dihapus."""
        from app.models.borrow_detail import BorrowDetail as BD
        deleted = db.query(BD).filter(BD.borrow_id.in_(ids)).delete(synchronize_session=False)
        return deleted

    def delete_return_details_by_transaction_ids(self, db: Session, ids: list[int]) -> int:
        """Hapus semua return_details yang terkait dengan daftar ID transaksi."""
        from app.models.return_detail import ReturnDetail
        from app.models.return_ import Return
        # Fetch IDs first (join not compatible with bulk delete)
        detail_ids = [
            row[0] for row in (
                db.query(ReturnDetail.id)
                .join(Return, ReturnDetail.return_id == Return.id)
                .filter(Return.borrow_id.in_(ids))
                .all()
            )
        ]
        if not detail_ids:
            return 0
        deleted = (
            db.query(ReturnDetail)
            .filter(ReturnDetail.id.in_(detail_ids))
            .delete(synchronize_session=False)
        )
        return deleted

    def delete_return_detail_items_by_transaction_ids(self, db: Session, ids: list[int]) -> int:
        """Hapus semua return_detail_items yang terkait dengan daftar ID transaksi."""
        from app.models.return_detail import ReturnDetail
        from app.models.return_detail_item import ReturnDetailItem
        from app.models.return_ import Return
        # Fetch IDs first (join not compatible with bulk delete)
        item_ids = [
            row[0] for row in (
                db.query(ReturnDetailItem.id)
                .join(ReturnDetail, ReturnDetailItem.return_detail_id == ReturnDetail.id)
                .join(Return, ReturnDetail.return_id == Return.id)
                .filter(Return.borrow_id.in_(ids))
                .all()
            )
        ]
        if not item_ids:
            return 0
        deleted = (
            db.query(ReturnDetailItem)
            .filter(ReturnDetailItem.id.in_(item_ids))
            .delete(synchronize_session=False)
        )
        return deleted

    def delete_returns_by_transaction_ids(self, db: Session, ids: list[int]) -> int:
        """Hapus semua return records yang terkait dengan daftar ID transaksi."""
        from app.models.return_ import Return
        deleted = db.query(Return).filter(Return.borrow_id.in_(ids)).delete(synchronize_session=False)
        return deleted

    def delete_activity_logs_by_transaction_ids(self, db: Session, ids: list[int]) -> int:
        """Hapus activity_logs terkait transaksi."""
        from app.models.activity_log import ActivityLog
        deleted = (
            db.query(ActivityLog)
            .filter(
                ActivityLog.reference_table == "borrow_transactions",
                ActivityLog.reference_id.in_(ids),
            )
            .delete(synchronize_session=False)
        )
        return deleted

    def delete_by_ids(self, db: Session, ids: list[int]) -> int:
        """Hapus transaksi berdasarkan daftar ID. Kembalikan jumlah yang dihapus."""
        deleted = (
            db.query(BorrowTransaction)
            .filter(BorrowTransaction.id.in_(ids))
            .delete(synchronize_session=False)
        )
        return deleted