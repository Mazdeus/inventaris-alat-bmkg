"""OfficerService — logika bisnis untuk pengelolaan data petugas."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.borrow_transaction import BorrowTransaction
from app.models.return_ import Return
from app.repositories.officer_repository import OfficerRepository
from app.schemas.officer import OfficerCreate, OfficerResponse, OfficerUpdate


class OfficerService:
    def __init__(self):
        self.repo = OfficerRepository()

    def _to_response(self, officer) -> OfficerResponse:
        return OfficerResponse(
            id=officer.id,
            officer_name=officer.officer_name,
            nip=officer.nip,
            phone=officer.phone,
            email=officer.email,
            position=officer.position,
            institution=officer.institution,
            is_active=officer.is_active,
            created_at=officer.created_at,
            updated_at=officer.updated_at,
        )

    def get_officer(self, db: Session, officer_id: int) -> OfficerResponse:
        officer = self.repo.get(db, officer_id)
        if not officer:
            raise HTTPException(status_code=404, detail="Data petugas tidak ditemukan")
        return self._to_response(officer)

    def get_officers(
        self, db: Session, *, page: int = 1, size: int = 10,
        search: str | None = None, is_active: bool | None = None,
    ):
        if search:
            all_officers = self.repo.search(db, search, skip=0, limit=10000)
        elif is_active is not None:
            filter_val = True if is_active else False
            all_officers = self.repo.get_active(db, skip=0, limit=10000) if filter_val else self.repo.get_multi(db, skip=0, limit=10000)
        else:
            all_officers = self.repo.get_multi(db, skip=0, limit=10000)

        total = len(all_officers)
        skip = (page - 1) * size

        # Apply pagination manually
        paginated = all_officers[skip:skip + size]
        return [self._to_response(o) for o in paginated], total

    def create_officer(self, db: Session, data: OfficerCreate) -> OfficerResponse:
        # Validasi NIP hanya angka
        if not data.nip.isdigit():
            raise HTTPException(status_code=400, detail="NIP harus berupa angka")

        # Validasi NIP unik
        existing = self.repo.get_by_nip(db, data.nip)
        if existing:
            raise HTTPException(status_code=409, detail=f"NIP '{data.nip}' sudah digunakan oleh petugas lain")

        officer = self.repo.create(db, data.model_dump())
        return self._to_response(officer)

    def update_officer(self, db: Session, officer_id: int, data: OfficerUpdate) -> OfficerResponse:
        officer = self.repo.get(db, officer_id)
        if not officer:
            raise HTTPException(status_code=404, detail="Data petugas tidak ditemukan")

        update_data = data.model_dump(exclude_unset=True)

        # Validasi NIP jika diubah
        if "nip" in update_data:
            nip = update_data["nip"]
            if not nip.isdigit():
                raise HTTPException(status_code=400, detail="NIP harus berupa angka")
            existing = self.repo.get_by_nip(db, nip)
            if existing and existing.id != officer_id:
                raise HTTPException(status_code=409, detail=f"NIP '{nip}' sudah digunakan oleh petugas lain")

        officer = self.repo.update(db, officer, update_data)
        return self._to_response(officer)

    def delete_officer(self, db: Session, officer_id: int) -> dict:
        """Hapus petugas. Hanya petugas yang TIDAK terkait transaksi yang bisa dihapus.
        Petugas yang masih terkait peminjaman/pengembalian/pelimpahan tidak bisa dihapus."""
        officer = self.repo.get(db, officer_id)
        if not officer:
            raise HTTPException(status_code=404, detail="Data petugas tidak ditemukan")

        # Cek apakah officer punya transaksi terkait
        has_borrows = db.query(BorrowTransaction).filter(
            BorrowTransaction.issued_by == officer_id
        ).count() > 0

        has_returns = db.query(Return).filter(
            Return.received_by == officer_id
        ).count() > 0

        has_handovers = False
        try:
            from app.models.handover import Handover
            has_handovers = db.query(Handover).filter(
                Handover.issued_by == officer_id
            ).count() > 0
        except Exception:
            pass

        officer_name = officer.officer_name

        if has_borrows or has_returns or has_handovers:
            raise HTTPException(
                status_code=409,
                detail=f"Petugas '{officer_name}' tidak bisa dihapus karena masih terkait dengan transaksi "
                       f"(peminjaman/pengembalian/pelimpahan).",
            )

        self.repo.delete(db, officer_id)
        return {"status": "success", "message": f"Petugas '{officer_name}' berhasil dihapus"}
