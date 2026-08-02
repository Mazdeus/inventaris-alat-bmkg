"""Schema BorrowExtension — request/response untuk perpanjangan peminjaman."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BorrowExtensionCreate(BaseModel):
    """Request body untuk mengajukan perpanjangan."""
    requested_return_date: date = Field(..., description="Tanggal kembali yang diajukan")
    reason: str = Field(..., min_length=1, description="Alasan perpanjangan")


class BorrowExtensionResponse(BaseModel):
    """Response untuk satu perpanjangan."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    borrow_id: int
    requested_by: Optional[int] = None
    requested_by_name: Optional[str] = None
    requested_return_date: date
    reason: Optional[str] = None
    status: str
    approved_by: Optional[int] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
