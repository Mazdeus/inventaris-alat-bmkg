"""OfficerRepository — query untuk tabel officers."""
from sqlalchemy.orm import Session

from app.models.officer import Officer
from app.repositories.base import BaseRepository


class OfficerRepository(BaseRepository[Officer]):
    def __init__(self):
        super().__init__(Officer)

    def get_active(self, db: Session, *, skip: int = 0, limit: int = 100) -> list[Officer]:
        return (
            db.query(Officer)
            .filter(Officer.is_active == True)
            .order_by(Officer.officer_name)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search(self, db: Session, name: str, *, skip: int = 0, limit: int = 100) -> list[Officer]:
        return (
            db.query(Officer)
            .filter(Officer.officer_name.ilike(f"%{name}%"))
            .order_by(Officer.officer_name)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_nip(self, db: Session, nip: str) -> Officer | None:
        return db.query(Officer).filter(Officer.nip == nip).first()
