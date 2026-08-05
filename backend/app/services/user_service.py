"""UserService — logika bisnis untuk pengelolaan user."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserUpdate


class UserService:
    def __init__(self):
        self.repo = UserRepository()

    def _to_response(self, user) -> UserResponse:
        """Konversi ORM object ke response schema."""
        return UserResponse(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            role=user.role.role_name if user.role else "Unknown",
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def get_user(self, db: Session, user_id: int) -> UserResponse:
        user = self.repo.get(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User tidak ditemukan")
        return self._to_response(user)

    def get_users(self, db: Session, page: int = 1, size: int = 10, is_active: bool | None = None):
        skip = (page - 1) * size
        if is_active is not None:
            users = self.repo.get_active_users(db, skip=skip, limit=size) if is_active else []
            total = self.repo.count_active_users(db) if is_active else 0
        else:
            users = self.repo.get_multi(db, skip=skip, limit=size)
            total = self.repo.count(db)
        return [self._to_response(u) for u in users], total

    def create_user(self, db: Session, data: UserCreate) -> UserResponse:
        existing = self.repo.get_by_username(db, data.username)
        if existing:
            raise HTTPException(status_code=409, detail=f"Username '{data.username}' sudah digunakan")

        user_data = data.model_dump()
        user_data["password"] = hash_password(user_data.pop("password"))
        user_data["role_id"] = 1  # Selalu Admin — hanya admin yang punya akun
        user = self.repo.create(db, user_data)
        return self._to_response(user)

    def update_user(self, db: Session, user_id: int, data: UserUpdate) -> UserResponse:
        user = self.repo.get(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User tidak ditemukan")

        update_data = data.model_dump(exclude_unset=True)
        # Cegah perubahan role — hanya admin yang punya akun
        update_data.pop("role_id", None)
        if "password" in update_data and update_data["password"]:
            update_data["password"] = hash_password(update_data["password"])

        user = self.repo.update(db, user, update_data)
        return self._to_response(user)

    def delete_user(self, db: Session, user_id: int) -> dict:
        user = self.repo.get(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User tidak ditemukan")

        has_transactions = bool(user.issued_transactions or user.received_returns or user.activity_logs)
        if has_transactions:
            self.repo.update(db, user, {"is_active": False})
            return {"status": "success", "message": f"User '{user.username}' dinonaktifkan (memiliki riwayat transaksi)"}

        self.repo.delete(db, user_id)
        return {"status": "success", "message": f"User '{user.username}' berhasil dihapus"}
