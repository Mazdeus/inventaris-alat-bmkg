"""Auth service — logika bisnis autentikasi."""
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token, generate_refresh_token, hash_refresh_token,
    verify_password, REFRESH_TOKEN_EXPIRE_DAYS,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import LoginResponse, UserInfo


class AuthService:
    def authenticate(self, db: Session, username: str, password: str):
        """Verifikasi kredensial user. Return User jika valid, None jika gagal."""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not user.is_active:
            return None
        if not verify_password(password, user.password):
            return None
        return user

    def login(self, db: Session, username: str, password: str) -> LoginResponse:
        """Login user — verifikasi kredensial dan generate access + refresh token."""
        user = self.authenticate(db, username, password)
        if not user:
            raise HTTPException(status_code=401, detail="Username atau password salah")

        token_data = {"sub": str(user.id), "username": user.username}
        access_token = create_access_token(token_data)

        # Generate refresh token
        refresh_token = generate_refresh_token()
        token_hash = hash_refresh_token(refresh_token)
        expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_obj = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(refresh_obj)
        db.commit()

        role_name = user.role.role_name if user.role else "User"

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=3600,
            user=UserInfo(
                id=user.id,
                username=user.username,
                full_name=user.full_name,
                role=role_name,
            ),
            refresh_token=refresh_token,
        )

    def refresh(self, db: Session, refresh_token: str) -> LoginResponse:
        """Refresh access token — validate refresh token, rotate, return new tokens."""
        token_hash = hash_refresh_token(refresh_token)

        stored = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
        ).first()

        if not stored or stored.revoked_at is not None:
            raise HTTPException(status_code=401, detail="Refresh token tidak valid")

        if stored.expires_at < datetime.utcnow():
            stored.revoked_at = datetime.utcnow()
            db.commit()
            raise HTTPException(status_code=401, detail="Refresh token sudah kadaluarsa")

        # Revoke old token
        stored.revoked_at = datetime.utcnow()

        # Get user
        user = db.query(User).filter(User.id == stored.user_id).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User tidak aktif")

        # Generate new tokens
        token_data = {"sub": str(user.id), "username": user.username}
        access_token = create_access_token(token_data)

        new_refresh = generate_refresh_token()
        new_hash = hash_refresh_token(new_refresh)
        new_expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        new_obj = RefreshToken(
            user_id=user.id,
            token_hash=new_hash,
            expires_at=new_expires,
        )
        db.add(new_obj)
        db.commit()

        role_name = user.role.role_name if user.role else "User"

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=3600,
            user=UserInfo(
                id=user.id,
                username=user.username,
                full_name=user.full_name,
                role=role_name,
            ),
            refresh_token=new_refresh,
        )