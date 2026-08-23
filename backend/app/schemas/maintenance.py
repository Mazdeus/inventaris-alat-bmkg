"""Schema Maintenance — request/response untuk riwayat perawatan."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MaintenanceCreate(BaseModel):
    inventory_component_id: int = Field(..., description="ID komponen yang dirawat")
    start_date: date = Field(..., description="Tanggal mulai perawatan")
    end_date: Optional[date] = Field(None, description="Tanggal selesai (wajib jika status Completed)")
    description: Optional[str] = Field(None, description="Deskripsi perawatan")
    status: str = Field(default="In Progress", min_length=1, max_length=50, description="Status perawatan")
    item_ids: list[int] = Field(..., min_length=1, description="ID item spesifik yang dirawat (minimal 1)")


class MaintenanceUpdate(BaseModel):
    end_date: Optional[date] = Field(None, description="Tanggal selesai")
    description: Optional[str] = None
    status: Optional[str] = Field(None, min_length=1, max_length=50)


class ComponentBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    item_name: str
    serial_number: Optional[str] = None
    status: Optional[str] = ""


class MaintenanceItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    inventory_item_id: int
    serial_number: Optional[str] = None
    previous_status: Optional[str] = None


class MaintenanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    component: Optional[ComponentBrief] = None
    start_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None
    status: str
    component_status: Optional[str] = None
    items: list[MaintenanceItemResponse] = []
