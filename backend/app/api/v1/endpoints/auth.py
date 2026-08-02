"""Auth endpoints — login, refresh token, current user info."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Union

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, decode_access_token
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, RefreshRequest, UserInfo
from app.services.activity_log_service import ActivityLogService
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def _get_client_ip(request: Request) -> str | None:
    """Get client IP from X-Forwarded-For header or request.client."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


@router.post("/login", response_model=LoginResponse)
def login(
    request: Request,
    login_request: Union[LoginRequest, None] = None,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login pengguna — menerima form data (Swagger Authorize) ATAU JSON body (API client).

    **Swagger Authorize:** Isi username dan password di popup — akan otomatis login dan simpan token.

    **API Client (React/curl):** Kirim JSON body:
    ```json
    {"username": "admin", "password": "admin123"}
    ```
    (FR-01, FR-02)
    """
    service = AuthService()
    log_svc = ActivityLogService()
    ip = _get_client_ip(request)
    ua = request.headers.get("User-Agent")

    if login_request is not None and login_request.username and login_request.password:
        result = service.login(db, login_request.username, login_request.password)
        log_svc.log(db, user_id=result.user.id,
                     activity=f"{result.user.full_name} login ke sistem",
                     ip_address=ip, user_agent=ua)
        return result

    if form_data.username and form_data.password:
        result = service.login(db, form_data.username, form_data.password)
        log_svc.log(db, user_id=result.user.id,
                     activity=f"{result.user.full_name} login ke sistem",
                     ip_address=ip, user_agent=ua)
        return result

    raise HTTPException(status_code=400, detail="Username dan password wajib diisi")


@router.post("/refresh")
def refresh_token(data: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token — validasi refresh token, rotate, return token baru."""
    service = AuthService()
    try:
        result = service.refresh(db, data.refresh_token)
        return result
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Refresh token tidak valid")


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Mendapatkan profil user yang sedang login."""
    return {
        "status": "success",
        "message": "Data user ditemukan",
        "data": UserInfo(
            id=current_user.id,
            username=current_user.username,
            full_name=current_user.full_name,
            role=current_user.role.role_name if current_user.role else "User",
        ).model_dump(),
    }


@router.post("/login/json", response_model=LoginResponse)
def login_json(req: Request, request: LoginRequest, db: Session = Depends(get_db)):
    """Alternatif login khusus JSON body — untuk API client yang tidak bisa kirim form data."""
    service = AuthService()
    log_svc = ActivityLogService()
    result = service.login(db, request.username, request.password)
    ip = _get_client_ip(req)
    ua = req.headers.get("User-Agent")
    log_svc.log(db, user_id=result.user.id,
                 activity=f"{result.user.full_name} login ke sistem",
                 ip_address=ip, user_agent=ua)
    return result