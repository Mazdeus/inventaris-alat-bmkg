"""Schema Return — request/response untuk transaksi pengembalian. (FR-23 s.d FR-27)"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ReturnDetailItemCreate(BaseModel):
    """Satu barang fisik yang dikembalikan — per SN."""
    inventory_item_id: int = Field(..., description="ID inventory_item (barang fisik)")
    condition: str = Field(..., min_length=1, max_length=50, description="Kondisi: Baik, Rusak")
    notes: Optional[str] = Field(None, description="Catatan kerusakan per barang")


class ReturnDetailCreate(BaseModel):
    """Ringkasan per komponen yang dikembalikan."""
    inventory_component_id: int = Field(..., description="ID komponen yang dikembalikan")
    items: list[ReturnDetailItemCreate] = Field(..., min_length=1, description="Daftar barang fisik per SN")


class ReturnCreate(BaseModel):
    """Request body untuk membuat pengembalian."""
    borrow_id: int = Field(..., description="ID transaksi pinjam yang dikembalikan")
    received_by: Optional[int] = Field(None, description="ID petugas yang menerima barang")
    return_date: date = Field(..., description="Tanggal pengembalian")
    photo: Optional[str] = Field(None, max_length=255, description="URL/path foto dokumentasi pengembalian")
    late_reason: Optional[str] = Field(None, description="Alasan keterlambatan (wajib jika terlambat)")
    details: list[ReturnDetailCreate] = Field(..., min_length=1, description="Daftar komponen yang dikembalikan")


class ReturnUpdate(BaseModel):
    """Request body untuk mengedit pengembalian (hanya status Menunggu)."""
    received_by: Optional[int] = Field(None, description="ID petugas yang menerima barang")
    return_date: Optional[date] = Field(None, description="Tanggal pengembalian")
    photo: Optional[str] = Field(None, max_length=255, description="URL/path foto dokumentasi pengembalian")
    late_reason: Optional[str] = Field(None, description="Alasan keterlambatan (wajib jika terlambat)")
    details: Optional[list[ReturnDetailCreate]] = Field(None, description="Daftar komponen yang dikembalikan (kondisi per barang)")


class ReturnDetailItemResponse(BaseModel):
    """Response untuk satu barang fisik yang dikembalikan."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    inventory_item_id: int
    serial_number: Optional[str] = None
    condition: str
    notes: Optional[str] = None
    status_after: Optional[str] = None


class ReturnDetailResponse(BaseModel):
    """Response per komponen yang dikembalikan."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    component: Optional[dict] = None
    quantity: int
    items: list[ReturnDetailItemResponse] = []


class ReturnResponse(BaseModel):
    """Detail response untuk satu pengembalian."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    borrow_transaction_id: Optional[int] = None
    borrow_id: Optional[int] = None
    borrower_name: Optional[str] = ""
    received_by: Optional[int] = None
    officer_name: Optional[str] = None
    return_date: date
    borrow_date: Optional[date] = None
    expected_return_date: Optional[date] = None
    is_late: bool = False
    days_late: int = 0
    status: Optional[str] = None
    photo: Optional[str] = None
    signed_document: Optional[str] = None
    late_reason: Optional[str] = None
    details: list[ReturnDetailResponse] = []
    transaction_status: Optional[str] = None
    created_at: Optional[datetime] = None
    extension: Optional[dict] = None  # ringkasan perpanjangan dari transaksi asal


class ReturnListResponse(BaseModel):
    """Ringkasan untuk daftar pengembalian."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    borrow_transaction_id: Optional[int] = None
    borrower_name: Optional[str] = ""
    received_by: Optional[int] = None
    officer_name: Optional[str] = ""
    return_date: date
    expected_return_date: Optional[date] = None
    status: Optional[str] = None
    is_late: bool = False
    days_late: int = 0
    items_count: int = 0
    total_items: int = 0
    details: list[ReturnDetailResponse] = []
