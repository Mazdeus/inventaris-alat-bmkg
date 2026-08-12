"""BorrowerService — logika bisnis untuk pengelolaan data peminjam."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.borrow_transaction import BorrowTransaction
from app.repositories.borrower_repository import BorrowerRepository
from app.schemas.borrower import BorrowerCreate, BorrowerResponse, BorrowerUpdate


class BorrowerService:
    def __init__(self):
        self.repo = BorrowerRepository()

    def _to_response(self, borrower) -> BorrowerResponse:
        return BorrowerResponse(
            id=borrower.id,
            borrower_type=borrower.borrower_type.value if hasattr(borrower.borrower_type, 'value') else borrower.borrower_type,
            borrower_name=borrower.borrower_name,
            institution=borrower.institution,
            phone=borrower.phone,
            address=borrower.address,
            nip=borrower.nip,
            email=borrower.email,
        )

    def get_borrower(self, db: Session, borrower_id: int) -> BorrowerResponse:
        borrower = self.repo.get(db, borrower_id)
        if not borrower:
            raise HTTPException(status_code=404, detail="Data peminjam tidak ditemukan")
        return self._to_response(borrower)

    def get_borrowers(
        self, db: Session, *, page: int = 1, size: int = 10,
        borrower_type: str | None = None, search: str | None = None,
    ):
        skip = (page - 1) * size
        if search:
            borrowers = self.repo.search_by_name(db, search, skip=skip, limit=size)
            total = len(self.repo.search_by_name(db, search, skip=0, limit=10000))
        elif borrower_type:
            borrowers = self.repo.get_by_type(db, borrower_type, skip=skip, limit=size)
            total = len(self.repo.get_by_type(db, borrower_type, skip=0, limit=10000))
        else:
            borrowers = self.repo.get_multi(db, skip=skip, limit=size)
            total = self.repo.count(db)
        return [self._to_response(b) for b in borrowers], total

    def create_borrower(self, db: Session, data: BorrowerCreate) -> BorrowerResponse:
        borrower = self.repo.create(db, data.model_dump())
        return self._to_response(borrower)

    def update_borrower(self, db: Session, borrower_id: int, data: BorrowerUpdate) -> BorrowerResponse:
        borrower = self.repo.get(db, borrower_id)
        if not borrower:
            raise HTTPException(status_code=404, detail="Data peminjam tidak ditemukan")
        borrower = self.repo.update(db, borrower, data.model_dump(exclude_unset=True))
        return self._to_response(borrower)

    def bulk_delete_borrowers(self, db: Session, ids: list[int]) -> dict:
        """Hapus banyak peminjam sekaligus.
        - Jika tidak ada transaksi → hard delete (benar-benar dihapus).
        - Jika ada transaksi → soft delete (set deleted_at, sembunyikan dari daftar).
        Untuk soft delete, NIP/email dimodifikasi agar tidak konflik dengan data baru."""
        from datetime import datetime
        not_found = []
        hard_deleted = []
        soft_deleted = []

        for borrower_id in ids:
            borrower = self.repo.get(db, borrower_id)
            if not borrower:
                not_found.append(borrower_id)
                continue

            # Cek apakah peminjam punya transaksi
            tx_count = db.query(BorrowTransaction).filter(
                BorrowTransaction.borrower_id == borrower_id
            ).count()

            if tx_count == 0:
                # Tidak ada transaksi → hard delete
                db.delete(borrower)
                hard_deleted.append(borrower_id)
            else:
                # Ada transaksi → soft delete + dedup NIP/email
                borrower.deleted_at = datetime.utcnow()
                # Modify unique fields agar tidak conflict dengan data baru
                if borrower.nip:
                    borrower.nip = f"{borrower.nip}_deleted_{borrower.id}"
                if borrower.email:
                    borrower.email = f"{borrower.email}_deleted_{borrower.id}"
                soft_deleted.append(borrower_id)

        db.commit()
        return {
            "deleted": len(hard_deleted) + len(soft_deleted),
            "hard_deleted": len(hard_deleted),
            "soft_deleted": len(soft_deleted),
            "not_found": len(not_found),
        }
