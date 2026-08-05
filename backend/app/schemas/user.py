"""Schema User — request/response untuk CRUD pengguna."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    """Schema untuk membuat admin baru — role otomatis Admin."""
    username: str = Field(..., min_length=3, max_length=50, description="Username unik")
    password: str = Field(..., min_length=6, max_length=255, description="Password (min 6 karakter)")
    full_name: str = Field(..., min_length=1, max_length=100, description="Nama lengkap")


class UserUpdate(BaseModel):
    """Schema untuk update admin — semua field opsional (partial update)."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=6, max_length=255)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema response — data user yang dikirim ke client (tanpa password!)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    role: str = Field(..., description="Nama role (Admin/User)")
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
