"""Schema Inventory — request/response untuk komponen inventaris."""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Component ──

class ComponentCreate(BaseModel):
    item_name: str = Field(..., min_length=1, max_length=100, description="Nama komponen")
    brand: str = Field(..., min_length=1, max_length=100, description="Merek")
    model: str = Field(..., min_length=1, max_length=100, description="Model")
    serial_number: Optional[str] = Field(None, max_length=100)
    procurement_year: int = Field(..., ge=2000, le=2100, description="Tahun Pengadaan")
    supplier: Optional[str] = Field(None, max_length=150)
    total_quantity: int = Field(..., gt=0, description="Jumlah total")
    specifications: Optional[str] = Field(None, description="Spesifikasi teknis komponen")
    photo_url: Optional[str] = Field(None, max_length=500, description="URL absolut foto (localhost)")
    photo_path: Optional[str] = Field(None, max_length=500, description="Path absolut filesystem foto")
    division: str = Field(..., min_length=1, max_length=50, description="Divisi: Gempa Bumi, Tsunami, Percepatan Tanah")
    serial_numbers: Optional[List[Optional[str]]] = Field(
        default_factory=list, description="Serial number untuk setiap barang fisik (sesuai quantity)"
    )
    notes: Optional[str] = None


class ComponentUpdate(BaseModel):
    item_name: Optional[str] = Field(None, min_length=1, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    procurement_year: Optional[int] = Field(None, ge=2000, le=2100)
    supplier: Optional[str] = Field(None, max_length=150)
    total_quantity: Optional[int] = Field(None, gt=0)
    specifications: Optional[str] = Field(None, description="Spesifikasi teknis komponen")
    photo_url: Optional[str] = Field(None, max_length=500, description="URL absolut foto (localhost)")
    photo_path: Optional[str] = Field(None, max_length=500, description="Path absolut filesystem foto")
    division: Optional[str] = Field(None, max_length=50)
    status_id: Optional[int] = None
    notes: Optional[str] = None
    serial_numbers: Optional[List[Optional[str]]] = Field(
        None, description="Serial number untuk barang baru (jika quantity bertambah)"
    )


class ComponentBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_name: str
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    total_quantity: int
    status: str = ""


class ComponentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_name: str
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    procurement_year: Optional[int] = None
    supplier: Optional[str] = None
    total_quantity: int
    specifications: str = ""
    photo_url: Optional[str] = None
    photo_path: Optional[str] = None
    division: str = ""
    available_quantity: int = 0
    status: str = ""
    notes: Optional[str] = None
    items: list["ItemResponse"] = []


# ── Item (per barang fisik) ──

class ItemUpdate(BaseModel):
    serial_number: Optional[str] = Field(None, max_length=100, description="Serial number per barang")
    status_id: Optional[int] = Field(None, description="ID status baru (hanya Available/Broken yang diizinkan)")


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inventory_component_id: int
    serial_number: Optional[str] = None
    status: str = ""
    notes: Optional[str] = None
