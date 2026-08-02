"""Activity Logs endpoint — audit trail (Admin only). (FR-28, FR-29, UR-10)"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.schemas.activity_log import ActivityLogResponse
from app.repositories.activity_log_repository import ActivityLogRepository

router = APIRouter(prefix="/api/v1/activity-logs", tags=["Activity Logs"])


@router.get("")
def list_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: int | None = Query(None),
    start_date: str | None = Query(None, description="Filter tanggal awal (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="Filter tanggal akhir (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Daftar log aktivitas — hanya Admin. (FR-28, FR-29)"""
    repo = ActivityLogRepository()
    from datetime import datetime as dt
    sd = dt.fromisoformat(start_date) if start_date else None
    ed = dt.fromisoformat(end_date) if end_date else None
    logs = repo.get_filtered(db, user_id=user_id, start_date=sd, end_date=ed,
                             skip=(page - 1) * size, limit=size)
    total = repo.count_filtered(db, user_id=user_id, start_date=sd, end_date=ed)
    data = []
    for log in logs:
        data.append(ActivityLogResponse(
            id=log.id, activity=log.activity,
            reference_table=log.reference_table, reference_id=log.reference_id,
            ip_address=log.ip_address, user_agent=log.user_agent,
            extra_data=log.extra_data,
            created_at=log.created_at,
            user={"id": log.user.id, "username": log.user.username, "full_name": log.user.full_name} if log.user else None,
        ).model_dump())
    return {
        "status": "success", "message": "Daftar log berhasil diambil", "data": data,
        "meta": {"page": page, "size": size, "total": total, "total_pages": max(1, (total + size - 1) // size)},
    }


@router.get("/{log_id}")
def get_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    repo = ActivityLogRepository()
    log = repo.get(db, log_id)
    if not log:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Log tidak ditemukan")
    return {
        "status": "success", "message": "Data log ditemukan",
        "data": ActivityLogResponse(
            id=log.id, activity=log.activity,
            reference_table=log.reference_table, reference_id=log.reference_id,
            created_at=log.created_at,
            user={"id": log.user.id, "username": log.user.username, "full_name": log.user.full_name} if log.user else None,
        ).model_dump(),
    }
