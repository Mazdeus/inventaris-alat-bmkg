"""Dependency injection — autentikasi dan otorisasi."""
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Mendapatkan user yang sedang login dari JWT token (wajib — 401 jika tidak ada)."""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Token tidak valid atau telah kedaluwarsa",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Akun tidak aktif")
    return user


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Mendapatkan user dari JWT token jika ada — return None jika tidak ada/tidak valid (public)."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        return None
    return user


def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Memastikan user memiliki role Admin."""
    if current_user.role.role_name != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Akses ditolak. Hanya Admin yang dapat mengakses",
        )
    return current_user