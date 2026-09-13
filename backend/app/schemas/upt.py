"""Schema UPT — request/response untuk data Unit Pelaksana Teknis (UPT)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UptCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150, description="Nama kantor / stasiun UPT BMKG (wajib)")
    address: Optional[str] = Field(None, description="Alamat UPT (opsional)")
    phone: Optional[str] = Field(None, max_length=50, description="Kontak / telepon UPT (opsional)")
    is_active: Optional[bool] = True


class UptUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150, description="Nama UPT")
    address: Optional[str] = Field(None, description="Alamat UPT")
    phone: Optional[str] = Field(None, max_length=50, description="Kontak / telepon UPT")
    is_active: Optional[bool] = None


class UptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
