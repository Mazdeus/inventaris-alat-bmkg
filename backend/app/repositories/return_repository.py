"""ReturnRepository — query untuk tabel returns."""
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.return_ import Return
from app.models.return_detail import ReturnDetail
from app.models.return_detail_item import ReturnDetailItem
from app.models.borrow_transaction import BorrowTransaction
from app.models.borrower import Borrower
from app.models.officer import Officer
from app.repositories.base import BaseRepository


class ReturnRepository(BaseRepository[Return]):
    def __init__(self):
        super().__init__(Return)

    def get_with_details(self, db: Session, return_id: int) -> Return | None:
        return (
            db.query(Return)
            .options(
                joinedload(Return.borrow_transaction).joinedload(BorrowTransaction.borrower),
                joinedload(Return.officer),
                joinedload(Return.return_details)
                    .joinedload(ReturnDetail.inventory_component),
                joinedload(Return.return_details)
                    .joinedload(ReturnDetail.return_detail_items)
                    .joinedload(ReturnDetailItem.inventory_item),
            )
            .filter(Return.id == return_id)
            .first()
        )

    def get_filtered(
        self, db: Session, *,
        start_date=None, end_date=None,
        search: str | None = None,
        skip=0, limit=100, order_dir="desc",
        **kwargs,
    ) -> list[Return]:
        order_col = Return.id.asc() if order_dir == "asc" else Return.id.desc()
        query = (
            db.query(Return)
            .options(
                joinedload(Return.borrow_transaction).joinedload(BorrowTransaction.borrower),
                joinedload(Return.officer),
            )
            .order_by(order_col)
        )
        if start_date:
            query = query.filter(Return.return_date >= start_date)
        if end_date:
            query = query.filter(Return.return_date <= end_date)
        if search:
            search_term = search.strip()
            query = (
                query
                .outerjoin(BorrowTransaction, Return.borrow_id == BorrowTransaction.id)
                .outerjoin(Borrower, BorrowTransaction.borrower_id == Borrower.id)
                .outerjoin(Officer, Return.received_by == Officer.id)
                .filter(
                    or_(
                        Return.transaction_number.ilike(f"%{search_term}%"),
                        BorrowTransaction.transaction_number.ilike(f"%{search_term}%"),
                        Borrower.borrower_name.ilike(f"%{search_term}%"),
                        Officer.officer_name.ilike(f"%{search_term}%"),
                    )
                )
            )
        return query.offset(skip).limit(limit).all()

    def count_filtered(
        self, db: Session, *,
        start_date=None, end_date=None,
        search: str | None = None,
        **kwargs,
    ) -> int:
        query = db.query(func.count(Return.id))
        if start_date:
            query = query.filter(Return.return_date >= start_date)
        if end_date:
            query = query.filter(Return.return_date <= end_date)
        if search:
            search_term = search.strip()
            query = (
                query
                .outerjoin(BorrowTransaction, Return.borrow_id == BorrowTransaction.id)
                .outerjoin(Borrower, BorrowTransaction.borrower_id == Borrower.id)
                .outerjoin(Officer, Return.received_by == Officer.id)
                .filter(
                    or_(
                        Return.transaction_number.ilike(f"%{search_term}%"),
                        BorrowTransaction.transaction_number.ilike(f"%{search_term}%"),
                        Borrower.borrower_name.ilike(f"%{search_term}%"),
                        Officer.officer_name.ilike(f"%{search_term}%"),
                    )
                )
            )
        return query.scalar() or 0
