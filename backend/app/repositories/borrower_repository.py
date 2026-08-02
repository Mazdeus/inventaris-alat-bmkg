"""BorrowerRepository — query khusus untuk tabel borrowers."""
from sqlalchemy.orm import Session

from app.models.borrower import Borrower
from app.repositories.base import BaseRepository


class BorrowerRepository(BaseRepository[Borrower]):
    def __init__(self):
        super().__init__(Borrower)

    def search_by_name(self, db: Session, name: str, *, skip: int = 0, limit: int = 100) -> list[Borrower]:
        return (
            db.query(Borrower)
            .filter(Borrower.borrower_name.ilike(f"%{name}%"))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_type(self, db: Session, borrower_type: str, *, skip: int = 0, limit: int = 100) -> list[Borrower]:
        return (
            db.query(Borrower)
            .filter(Borrower.borrower_type == borrower_type)
            .offset(skip)
            .limit(limit)
            .all()
        )
