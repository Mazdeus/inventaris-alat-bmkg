"""OfficerRepository — query untuk tabel officers."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.officer import Officer
from app.repositories.base import BaseRepository


class OfficerRepository(BaseRepository[Officer]):
    def __init__(self):
        super().__init__(Officer)

    def _exclude_deleted(self, query):
        """Exclude soft-deleted officers."""
        return query.filter(Officer.deleted_at.is_(None))

    def get(self, db: Session, id: int) -> Officer | None:
        return self._exclude_deleted(
            db.query(Officer).filter(Officer.id == id)
        ).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> list[Officer]:
        return self._exclude_deleted(
            db.query(Officer)
        ).offset(skip).limit(limit).all()

    def get_active(self, db: Session, *, skip: int = 0, limit: int = 100) -> list[Officer]:
        return (
            self._exclude_deleted(
                db.query(Officer).filter(Officer.is_active == True)
            )
            .order_by(Officer.officer_name)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search(self, db: Session, name: str, *, skip: int = 0, limit: int = 100) -> list[Officer]:
        return (
            self._exclude_deleted(
                db.query(Officer).filter(Officer.officer_name.ilike(f"%{name}%"))
            )
            .order_by(Officer.officer_name)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_nip(self, db: Session, nip: str) -> Officer | None:
        return db.query(Officer).filter(Officer.nip == nip).first()

    def count(self, db: Session) -> int:
        return self._exclude_deleted(
            db.query(func.count(Officer.id))
        ).scalar() or 0
