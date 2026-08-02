"""Schema Borrower — request/response untuk data peminjam."""
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class BorrowerCreate(BaseModel):
    borrower_type: Literal["Internal", "External"] = Field(..., description="Tipe peminjam")
    borrower_name: str = Field(..., min_length=1, max_length=100, description="Nama peminjam")
    institution: Optional[str] = Field(None, max_length=150, description="Nama institusi/perusahaan")
    phone: Optional[str] = Field(None, max_length=20, description="Nomor telepon")
    address: Optional[str] = Field(None, description="Alamat")
    nip: Optional[str] = Field(None, max_length=30, description="NIP/NIK")
    email: Optional[str] = Field(None, max_length=100, description="Email")


class BorrowerUpdate(BaseModel):
    borrower_type: Optional[Literal["Internal", "External"]] = None
    borrower_name: Optional[str] = Field(None, min_length=1, max_length=100)
    institution: Optional[str] = Field(None, max_length=150)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    nip: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=100)


class BorrowerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    borrower_type: str
    borrower_name: str
    institution: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    nip: Optional[str] = None
    email: Optional[str] = None
