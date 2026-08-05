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
        """Hapus petugas. Hanya bisa jika tidak terlibat transaksi aktif (Menunggu/Dipinjam)."""
        officer = self.repo.get(db, officer_id)
        if not officer:
            raise HTTPException(status_code=404, detail="Data petugas tidak ditemukan")

        # Cek apakah officer terhubung ke transaksi peminjaman aktif
        active_borrows = db.query(BorrowTransaction).filter(
            BorrowTransaction.issued_by == officer_id,
            BorrowTransaction.status.in_(["Menunggu", "Dipinjam"]),
        ).count()

        if active_borrows > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Petugas tidak bisa dihapus karena masih terhubung ke {active_borrows} transaksi peminjaman yang aktif (Menunggu/Dipinjam)",
            )

        # Cek apakah officer terhubung ke pengembalian di transaksi aktif
        active_returns = (
            db.query(Return)
            .join(BorrowTransaction, Return.borrow_id == BorrowTransaction.id)
            .filter(
                Return.received_by == officer_id,
                BorrowTransaction.status.in_(["Menunggu", "Dipinjam"]),
            )
            .count()
        )

        if active_returns > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Petugas tidak bisa dihapus karena masih terhubung ke {active_returns} pengembalian pada transaksi aktif (Menunggu/Dipinjam)",
            )

        # Hapus petugas — FK akan SET NULL untuk transaksi lama
        self.repo.delete(db, officer_id)
        return {"status": "success", "message": f"Petugas '{officer.officer_name}' berhasil dihapus"}
