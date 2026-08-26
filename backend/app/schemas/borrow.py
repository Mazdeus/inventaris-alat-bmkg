"""Schema Borrow — request/response untuk transaksi peminjaman."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ── Request ──

class BorrowDetailCreate(BaseModel):
    inventory_component_id: int = Field(..., description="ID komponen yang dipinjam")
    inventory_item_ids: list[int] = Field(..., min_length=1, description="ID item fisik (SN) yang dipilih")
    quantity: Optional[int] = Field(None, gt=0, description="Jumlah yang dipinjam (auto dari len(inventory_item_ids))")


class BorrowTransactionCreate(BaseModel):
    borrower_id: int = Field(..., description="ID peminjam")
    issued_by: Optional[int] = Field(None, description="ID petugas yang mengeluarkan barang")
    borrow_date: date = Field(..., description="Tanggal peminjaman")
    expected_return_date: date = Field(..., description="Tanggal rencana pengembalian")
    photo: Optional[str] = Field(None, max_length=255, description="URL/path foto dokumentasi peminjaman")
    item_description: str = Field(..., min_length=1, description="Deskripsi barang yang dipinjam (wajib)")
    purpose: str = Field(..., min_length=1, description="Tujuan peminjaman (wajib)")
    details: list[BorrowDetailCreate] = Field(..., min_length=1, description="Daftar komponen yang dipinjam")
    # status tidak dikirim — otomatis "Menunggu"

    @model_validator(mode="after")
    def validate_dates(self):
        if self.expected_return_date < self.borrow_date:
            raise ValueError("Tanggal rencana pengembalian harus >= tanggal peminjaman")
        return self


class ApprovalUpdate(BaseModel):
    reason: Optional[str] = Field(None, description="Alasan approve/reject")


class BorrowDetailUpdate(BaseModel):
    inventory_component_id: int = Field(..., description="ID komponen yang dipinjam")
    inventory_item_ids: list[int] = Field(..., min_length=1, description="ID item fisik (SN) yang dipilih")
    quantity: Optional[int] = Field(None, gt=0, description="Jumlah yang dipinjam")


class BorrowTransactionUpdate(BaseModel):
    """Update transaksi peminjaman. Untuk status Menunggu: semua field boleh diubah.
    Untuk status Dipinjam: hanya expected_return_date & issued_by."""
    borrower_id: Optional[int] = Field(None, description="ID peminjam")
    issued_by: Optional[int] = Field(None, description="ID petugas yang mengeluarkan")
    borrow_date: Optional[date] = Field(None, description="Tanggal peminjaman")
    expected_return_date: Optional[date] = Field(None, description="Tanggal rencana pengembalian")
    photo: Optional[str] = Field(None, max_length=255, description="URL/path foto dokumentasi")
    item_description: Optional[str] = Field(None, min_length=1, description="Deskripsi barang yang dipinjam")
    purpose: Optional[str] = Field(None, min_length=1, description="Tujuan peminjaman")
    details: Optional[list[BorrowDetailUpdate]] = Field(None, description="Daftar komponen yang dipinjam")


class BulkDeleteRequest(BaseModel):
    """Request body untuk bulk delete transaksi — Admin only."""
    ids: list[int] = Field(..., min_length=1, description="Daftar ID transaksi yang akan dihapus")


# ── Response ──

class BorrowerBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    borrower_name: str
    borrower_type: Optional[str] = None


class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str


class OfficerBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    officer_name: str


class ComponentBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    item_name: str
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    total_quantity: Optional[int] = None
    status: Optional[str] = None


class SelectedItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    serial_number: Optional[str] = None


class BorrowDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    component: Optional[ComponentBrief] = None
    quantity: int
    selected_items: list[SelectedItemResponse] = []


class BorrowTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    transaction_number: Optional[str] = None
    daily_sequence: Optional[int] = None
    borrower: Optional[BorrowerBrief] = None
    officer: Optional[OfficerBrief] = None
    issued_by: Optional[int] = None
    borrow_date: date
    expected_return_date: date
    status: str
    photo: Optional[str] = None
    signed_document: Optional[str] = None
    item_description: Optional[str] = None
    purpose: Optional[str] = None
    details: list[BorrowDetailResponse] = []
    created_at: Optional[datetime] = None
    extension: Optional[dict] = None  # ringkasan perpanjangan: {id, status, old_date, new_date, reason}


class BorrowTransactionListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    transaction_number: Optional[str] = None
    daily_sequence: Optional[int] = None
    borrower: Optional[BorrowerBrief] = None
    issued_by: Optional[int] = None
    officer_name: Optional[str] = None
    borrow_date: date
    expected_return_date: date
    status: str
    signed_document: Optional[str] = None
    items_count: int = 0
    total_items: int = 0
    details: list[BorrowDetailResponse] = []
    created_at: Optional[datetime] = None
