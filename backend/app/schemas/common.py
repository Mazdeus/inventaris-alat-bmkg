"""Schema umum — response wrapper dan pagination."""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseWrapper(BaseModel):
    """Bungkus standar untuk semua response API."""
    status: str = "success"
    message: str = "OK"
    data: Any = None


class PaginationParams(BaseModel):
    """Parameter pagination untuk endpoint list."""
    page: int = Field(default=1, ge=1, description="Halaman saat ini")
    size: int = Field(default=10, ge=1, le=100, description="Jumlah data per halaman")

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.size


class PaginationMeta(BaseModel):
    page: int
    size: int
    total: int
    total_pages: int
