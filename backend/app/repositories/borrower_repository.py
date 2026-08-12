"""BorrowerRepository — query khusus untuk tabel borrowers."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.borrower import Borrower
from app.repositories.base import BaseRepository


class BorrowerRepository(BaseRepository[Borrower]):
    def __init__(self):
        super().__init__(Borrower)

    def _exclude_deleted(self, query):
        """Exclude soft-deleted borrowers."""
        return query.filter(Borrower.deleted_at.is_(None))

    def get(self, db: Session, id: int) -> Borrower | None:
        return self._exclude_deleted(
            db.query(Borrower).filter(Borrower.id == id)
        ).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> list[Borrower]:
        return self._exclude_deleted(
            db.query(Borrower)
        ).offset(skip).limit(limit).all()

    def search_by_name(self, db: Session, name: str, *, skip: int = 0, limit: int = 100) -> list[Borrower]:
        return self._exclude_deleted(
            db.query(Borrower)
            .filter(Borrower.borrower_name.ilike(f"%{name}%"))
        ).offset(skip).limit(limit).all()

    def get_by_type(self, db: Session, borrower_type: str, *, skip: int = 0, limit: int = 100) -> list[Borrower]:
        return self._exclude_deleted(
            db.query(Borrower)
            .filter(Borrower.borrower_type == borrower_type)
        ).offset(skip).limit(limit).all()

    def count(self, db: Session) -> int:
        return self._exclude_deleted(
            db.query(func.count(Borrower.id))
        ).scalar() or 0
