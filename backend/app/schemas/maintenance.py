"""Schema Maintenance — request/response untuk riwayat perbaikan."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MaintenanceCreate(BaseModel):
    inventory_component_id: int = Field(..., description="ID komponen yang diperbaiki")
    start_date: date = Field(..., description="Tanggal mulai perbaikan")
    description: Optional[str] = Field(None, description="Deskripsi perbaikan")
    status: str = Field(default="In Progress", min_length=1, max_length=50, description="Status perbaikan")
    item_ids: Optional[list[int]] = Field(None, description="ID item spesifik yang diperbaiki (kosong = semua)")


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


class MaintenanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    component: Optional[ComponentBrief] = None
    start_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None
    status: str
    component_status: Optional[str] = None
