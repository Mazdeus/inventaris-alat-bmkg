"""UptService — logika bisnis untuk pengelolaan data UPT BMKG."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.upt import Upt
from app.repositories.upt_repository import UptRepository
from app.schemas.upt import UptCreate, UptResponse, UptUpdate
from app.services.activity_log_service import ActivityLogService
from app.core.logging_config import get_logger

logger = get_logger()


class UptService:
    def __init__(self):
        self.repo = UptRepository()
        self.log_svc = ActivityLogService()

    def _to_response(self, upt: Upt) -> UptResponse:
        return UptResponse(
            id=upt.id,
            name=upt.name,
            address=upt.address,
            phone=upt.phone,
            is_active=upt.is_active,
            created_at=upt.created_at,
            updated_at=upt.updated_at,
        )

    def get_upt(self, db: Session, upt_id: int) -> UptResponse:
        upt = self.repo.get(db, upt_id)
        if not upt:
            raise HTTPException(status_code=404, detail="Data UPT tidak ditemukan")
        return self._to_response(upt)

    def get_upts(
        self,
        db: Session,
        *,
        page: int = 1,
        size: int = 10,
        search: str | None = None,
        is_active: bool | None = None,
        order_dir: str = "asc",
    ) -> tuple[list[UptResponse], int]:
        upts, total = self.repo.get_paged(
            db, page=page, size=size, search=search, is_active=is_active, order_dir=order_dir
        )
        return [self._to_response(u) for u in upts], total

    def get_active_upts(self, db: Session, limit: int = 100) -> list[UptResponse]:
        upts = self.repo.get_active(db, limit=limit)
        return [self._to_response(u) for u in upts]

    def create_upt(self, db: Session, data: UptCreate, current_user=None) -> UptResponse:
        name_clean = data.name.strip()
        existing = self.repo.get_by_name(db, name_clean)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"UPT dengan nama '{name_clean}' sudah terdaftar"
            )

        payload = data.model_dump()
        payload["name"] = name_clean
        upt = self.repo.create(db, payload)

        # Log aktivitas
        user_name = current_user.full_name if current_user else "Admin"
        self.log_svc.log(
            db=db,
            user_id=current_user.id if current_user else None,
            activity=f"{user_name} menambahkan data UPT: {upt.name}",
            reference_table="upts",
            reference_id=upt.id,
            reference_path="/upts",
            extra_data=f"Nama: {upt.name}, Alamat: {upt.address or '-'}, Kontak: {upt.phone or '-'}",
        )
        return self._to_response(upt)

    def update_upt(self, db: Session, upt_id: int, data: UptUpdate, current_user=None) -> UptResponse:
        upt = self.repo.get(db, upt_id)
        if not upt:
            raise HTTPException(status_code=404, detail="Data UPT tidak ditemukan")

        if data.name:
            name_clean = data.name.strip()
            existing = self.repo.get_by_name(db, name_clean)
            if existing and existing.id != upt.id:
                raise HTTPException(
                    status_code=409,
                    detail=f"UPT dengan nama '{name_clean}' sudah terdaftar"
                )

        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if "name" in update_data:
            update_data["name"] = update_data["name"].strip()

        upt = self.repo.update(db, upt, update_data)

        # Log aktivitas
        user_name = current_user.full_name if current_user else "Admin"
        new_desc = f"Nama: {upt.name}, Alamat: {upt.address or '-'}, Kontak: {upt.phone or '-'}"
        self.log_svc.log(
            db=db,
            user_id=current_user.id if current_user else None,
            activity=f"{user_name} memperbarui data UPT: {upt.name}",
            reference_table="upts",
            reference_id=upt.id,
            reference_path="/upts",
            extra_data=new_desc,
        )
        return self._to_response(upt)

    def delete_upt(self, db: Session, upt_id: int, current_user=None) -> dict:
        upt = self.repo.get(db, upt_id)
        if not upt:
            raise HTTPException(status_code=404, detail="Data UPT tidak ditemukan")

        name = upt.name
        self.repo.soft_delete(db, upt)

        # Log aktivitas
        user_name = current_user.full_name if current_user else "Admin"
        self.log_svc.log(
            db=db,
            user_id=current_user.id if current_user else None,
            activity=f"{user_name} menghapus data UPT: {name}",
            reference_table="upts",
            reference_id=upt_id,
            reference_path="/upts",
        )
        return {"status": "success", "message": f"Data UPT '{name}' berhasil dihapus"}
