"""UserRepository — query khusus untuk tabel users."""
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    def get_by_username(self, db: Session, username: str) -> User | None:
        return db.query(User).filter(User.username == username).first()

    def get_active_users(self, db: Session, *, skip: int = 0, limit: int = 100) -> list[User]:
        return db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()

    def count_active_users(self, db: Session) -> int:
        return db.query(User).filter(User.is_active == True).count()
