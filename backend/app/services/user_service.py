"""UserService — logika bisnis untuk pengelolaan user."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.activity_log_service import ActivityLogService
from app.core.logging_config import get_logger

logger = get_logger()


class UserService:
    def __init__(self):
        self.repo = UserRepository()
        self.log_svc = ActivityLogService()

    def _to_response(self, user) -> UserResponse:
        """Konversi ORM object ke response schema."""
        return UserResponse(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            phone=user.phone,
            email=user.email,
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

    def create_user(self, db: Session, data: UserCreate, current_user=None) -> UserResponse:
        existing = self.repo.get_by_username(db, data.username)
        if existing:
            raise HTTPException(status_code=409, detail=f"Username '{data.username}' sudah digunakan")

        # Cek email duplikat
        from app.models.user import User
        email_exists = db.query(User).filter(User.email == data.email).first()
        if email_exists:
            raise HTTPException(status_code=409, detail=f"Email '{data.email}' sudah digunakan")

        user_data = data.model_dump()
        user_data["password"] = hash_password(user_data.pop("password"))
        user_data["role_id"] = 1  # Selalu Admin — hanya admin yang punya akun
        user = self.repo.create(db, user_data)

        if current_user is not None:
            logger.info("Admin '%s' ditambahkan oleh %s", user.full_name, current_user.full_name)
            self.log_svc.log(db, user_id=current_user.id,
                             activity=f"{current_user.full_name} menambah admin baru '{user.full_name}'",
                             reference_table="users", reference_id=user.id,
                             reference_path="/users")

        return self._to_response(user)

    def update_user(self, db: Session, user_id: int, data: UserUpdate) -> UserResponse:
        user = self.repo.get(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User tidak ditemukan")

        update_data = data.model_dump(exclude_unset=True)

        # Cek email duplikat (kecuali email milik user ini sendiri)
        if update_data.get("email") and update_data["email"] != user.email:
            from app.models.user import User
            email_exists = db.query(User).filter(
                User.email == update_data["email"],
                User.id != user_id,
            ).first()
            if email_exists:
                raise HTTPException(status_code=409, detail=f"Email '{update_data['email']}' sudah digunakan")

        # Validasi phone hanya angka
        if update_data.get("phone"):
            import re
            if not re.match(r"^[0-9]+$", update_data["phone"]):
                raise HTTPException(status_code=400, detail="Nomor HP hanya boleh berisi angka (0-9)")

        # Validasi email mengandung @
        if update_data.get("email"):
            import re
            if not re.match(r"^[^@\s]+@[^@\s]+$", update_data["email"]):
                raise HTTPException(status_code=400, detail="Email tidak valid (harus mengandung @)")

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

        # Cek riwayat user dari tabel-tabel yang benar-benar mereferensikan users
        from app.models.activity_log import ActivityLog
        from app.models.item_status_history import ItemStatusHistory
        from app.models.refresh_token import RefreshToken
        from app.models.transaction_snapshot import TransactionSnapshot

        activity_count = db.query(ActivityLog).filter(ActivityLog.user_id == user_id).count()
        history_count = db.query(ItemStatusHistory).filter(ItemStatusHistory.user_id == user_id).count()
        extension_count = len(user.requested_extensions or []) + len(user.approved_extensions or [])
        snapshot_count = db.query(TransactionSnapshot).filter(TransactionSnapshot.archived_by == user_id).count()

        has_history = (activity_count > 0 or history_count > 0
                       or extension_count > 0 or snapshot_count > 0)

        if has_history:
            # Punya riwayat → soft delete (nonaktifkan), karena FK activity_logs bersifat RESTRICT
            self.repo.update(db, user, {"is_active": False})
            logger.info("Admin '%s' dinonaktifkan (punya riwayat transaksi)", user.username)
            return {"status": "success", "message": f"User '{user.username}' dinonaktifkan (memiliki riwayat transaksi)"}

        # Tidak punya riwayat → hapus refresh token dulu (FK RESTRICT), lalu hard delete
        db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()
        db.flush()

        self.repo.delete(db, user_id)
        logger.info("Admin '%s' dihapus", user.username)
        return {"status": "success", "message": f"User '{user.username}' berhasil dihapus"}
