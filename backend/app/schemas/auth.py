"""Schema autentikasi — request dan response untuk login, token."""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username pengguna")
    password: str = Field(..., min_length=6, max_length=255, description="Password pengguna")


class UserInfo(BaseModel):
    id: int
    username: str
    full_name: str
    role: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo
    refresh_token: str = ""


class RefreshRequest(BaseModel):
    refresh_token: str