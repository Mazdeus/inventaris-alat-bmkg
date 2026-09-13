"""Schema Maintenance — request/response untuk riwayat pemeliharaan."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MaintenanceCreate(BaseModel):
    inventory_component_id: int = Field(..., description="ID komponen yang dirawat")
    officer_id: int = Field(..., description="ID petugas yang melakukan pemeliharaan (wajib)")
    start_date: date = Field(..., description="Tanggal mulai pemeliharaan")
    end_date: Optional[date] = Field(None, description="Tanggal selesai (wajib jika status Completed)")
    description: Optional[str] = Field(None, description="Deskripsi pemeliharaan")
    status: str = Field(default="In Progress", min_length=1, max_length=50, description="Status pemeliharaan")
    item_ids: list[int] = Field(..., min_length=1, description="ID item spesifik yang dirawat (minimal 1)")


class MaintenanceUpdate(BaseModel):
    officer_id: Optional[int] = Field(None, description="ID petugas yang melakukan pemeliharaan")
    end_date: Optional[date] = Field(None, description="Tanggal selesai")
    description: Optional[str] = None
    status: Optional[str] = Field(None, min_length=1, max_length=50)


class ComponentBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    item_name: str
    serial_number: Optional[str] = None
    status: Optional[str] = ""


class MaintenanceOfficerBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    officer_name: str


class MaintenanceItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    inventory_item_id: int
    serial_number: Optional[str] = None
    previous_status: Optional[str] = None


class MaintenanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    transaction_number: Optional[str] = None
    daily_sequence: Optional[int] = None
    component: Optional[ComponentBrief] = None
    officer: Optional[MaintenanceOfficerBrief] = None
    start_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None
    status: str
    component_status: Optional[str] = None
    items: list[MaintenanceItemResponse] = []
