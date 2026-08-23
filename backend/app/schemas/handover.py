"""Schema Handover — request/response untuk transaksi pelimpahan."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Request ──

class HandoverItemCreate(BaseModel):
    inventory_item_id: int = Field(..., description="ID item fisik (SN) yang dilimpahkan")


class HandoverCreate(BaseModel):
    upt_receiver: str = Field(..., min_length=1, max_length=100, description="UPT penerima barang")
    issued_by: Optional[int] = Field(None, description="ID petugas yang menyerahkan")
    handover_date: date = Field(..., description="Tanggal pelimpahan")
    photo: Optional[str] = Field(None, max_length=255, description="URL/path foto dokumentasi")
    notes: Optional[str] = Field(None, description="Catatan pelimpahan")
    items: list[HandoverItemCreate] = Field(..., min_length=1, description="Daftar barang yang dilimpahkan")


class HandoverUpdate(BaseModel):
    """Update pelimpahan (hanya status Draft)."""
    upt_receiver: Optional[str] = Field(None, min_length=1, max_length=100, description="UPT penerima barang")
    issued_by: Optional[int] = Field(None, description="ID petugas yang menyerahkan")
    handover_date: Optional[date] = Field(None, description="Tanggal pelimpahan")
    photo: Optional[str] = Field(None, max_length=255, description="URL/path foto dokumentasi")
    notes: Optional[str] = Field(None, description="Catatan pelimpahan")
    items: Optional[list[HandoverItemCreate]] = Field(None, description="Daftar barang yang dilimpahkan")


# ── Response ──

class HandoverItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    inventory_item_id: int
    serial_number: Optional[str] = None
    component_name: str = ""


class HandoverResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    upt_receiver: str
    issued_by: Optional[int] = None
    officer_name: Optional[str] = None
    handover_date: date
    status: str
    photo: Optional[str] = None
    signed_document: Optional[str] = None
    notes: Optional[str] = None
    items: list[HandoverItemResponse] = []
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class HandoverListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    upt_receiver: str
    handover_date: date
    status: str
    items_count: int = 0
    officer_name: Optional[str] = None
    created_at: Optional[datetime] = None
