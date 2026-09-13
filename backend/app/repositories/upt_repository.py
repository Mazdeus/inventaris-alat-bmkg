"""UptRepository — data access layer untuk tabel upts."""
from datetime import datetime
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.upt import Upt
from app.repositories.base import BaseRepository


class UptRepository(BaseRepository[Upt]):
    def __init__(self):
        super().__init__(Upt)

    def _exclude_deleted(self, query):
        """Exclude soft-deleted UPT records."""
        return query.filter(Upt.deleted_at.is_(None))

    def get(self, db: Session, id: int) -> Upt | None:
        return self._exclude_deleted(
            db.query(Upt).filter(Upt.id == id)
        ).first()

    def get_by_name(self, db: Session, name: str) -> Upt | None:
        return self._exclude_deleted(
            db.query(Upt).filter(func.lower(Upt.name) == name.strip().lower())
        ).first()

    def get_paged(
        self,
        db: Session,
        *,
        page: int = 1,
        size: int = 10,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Upt], int]:
        query = self._exclude_deleted(db.query(Upt))

        if is_active is not None:
            query = query.filter(Upt.is_active == is_active)

        if search:
            s = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Upt.name.ilike(s),
                    Upt.address.ilike(s),
                    Upt.phone.ilike(s),
                )
            )

        total = query.with_entities(func.count(Upt.id)).scalar() or 0
        upts = (
            query.order_by(Upt.name.asc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        return upts, total

    def get_active(self, db: Session, *, limit: int = 100) -> list[Upt]:
        return (
            self._exclude_deleted(
                db.query(Upt).filter(Upt.is_active == True)
            )
            .order_by(Upt.name.asc())
            .limit(limit)
            .all()
        )

    def soft_delete(self, db: Session, upt: Upt) -> Upt:
        upt.deleted_at = datetime.utcnow()
        upt.is_active = False
        db.commit()
        db.refresh(upt)
        return upt
