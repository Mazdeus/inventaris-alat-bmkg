"""ReturnRepository — query untuk tabel returns."""
from sqlalchemy.orm import Session, joinedload

from app.models.return_ import Return
from app.models.return_detail import ReturnDetail
from app.models.return_detail_item import ReturnDetailItem
from app.models.borrow_transaction import BorrowTransaction
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

    def get_filtered(self, db: Session, *, start_date=None, end_date=None, skip=0, limit=100, order_dir="desc", **kwargs) -> list[Return]:
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
        return query.offset(skip).limit(limit).all()
