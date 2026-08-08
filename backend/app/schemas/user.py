"""Schema User — request/response untuk CRUD pengguna."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserCreate(BaseModel):
    """Schema untuk membuat admin baru — role otomatis Admin."""
    username: str = Field(..., min_length=3, max_length=50, description="Username unik")
    password: str = Field(..., min_length=6, max_length=255, description="Password (min 6 karakter)")
    full_name: str = Field(..., min_length=1, max_length=100, description="Nama lengkap")
    phone: str = Field(..., min_length=6, max_length=20, description="Nomor HP (hanya angka)")
    email: str = Field(..., min_length=5, max_length=100, description="Email (harus mengandung @)")

    @field_validator("phone")
    @classmethod
    def phone_must_be_digits(cls, v: str) -> str:
        import re
        if not re.match(r"^[0-9]+$", v):
            raise ValueError("Nomor HP hanya boleh berisi angka (0-9)")
        return v

    @field_validator("email")
    @classmethod
    def email_must_contain_at(cls, v: str) -> str:
        import re
        if not re.match(r"^[^@\s]+@[^@\s]+$", v):
            raise ValueError("Email tidak valid (harus mengandung @)")
        return v


class UserUpdate(BaseModel):
    """Schema untuk update admin — semua field opsional (partial update)."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=6, max_length=255)
    phone: Optional[str] = Field(None, min_length=6, max_length=20)
    email: Optional[str] = Field(None, min_length=5, max_length=100)
    is_active: Optional[bool] = None

    @field_validator("phone")
    @classmethod
    def phone_must_be_digits(cls, v: str | None) -> str | None:
        import re
        if v is None:
            return v
        if not re.match(r"^[0-9]+$", v):
            raise ValueError("Nomor HP hanya boleh berisi angka (0-9)")
        return v

    @field_validator("email")
    @classmethod
    def email_must_contain_at(cls, v: str | None) -> str | None:
        import re
        if v is None:
            return v
        if not re.match(r"^[^@\s]+@[^@\s]+$", v):
            raise ValueError("Email tidak valid (harus mengandung @)")
        return v


class UserResponse(BaseModel):
    """Schema response — data user yang dikirim ke client (tanpa password!)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    role: str = Field(..., description="Nama role (Admin/User)")
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
