"""Schema Officer — request/response untuk data petugas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OfficerCreate(BaseModel):
    officer_name: str = Field(..., min_length=1, max_length=100, description="Nama petugas")
    nip: str = Field(..., min_length=1, max_length=30, description="NIP petugas (wajib, angka)")
    phone: Optional[str] = Field(None, max_length=20, description="Nomor telepon")
    email: Optional[str] = Field(None, max_length=100, description="Email")
    position: Optional[str] = Field(None, max_length=100, description="Jabatan")
    institution: str = Field(..., min_length=1, max_length=150, description="Instansi/unit kerja petugas (wajib)")


class OfficerUpdate(BaseModel):
    officer_name: Optional[str] = Field(None, min_length=1, max_length=100)
    nip: Optional[str] = Field(None, min_length=1, max_length=30)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    institution: Optional[str] = Field(None, min_length=1, max_length=150)
    is_active: Optional[bool] = None


class OfficerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    officer_name: str
    nip: str
    phone: Optional[str] = None
    email: Optional[str] = None
    position: Optional[str] = None
    institution: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
