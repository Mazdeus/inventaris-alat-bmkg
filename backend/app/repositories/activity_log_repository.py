"""ActivityLogRepository — query read-only untuk activity_logs."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.repositories.base import BaseRepository


class ActivityLogRepository(BaseRepository[ActivityLog]):
    def __init__(self):
        super().__init__(ActivityLog)

    def get_filtered(
        self, db: Session, *,
        user_id: int | None = None,
        start_date=None, end_date=None,
        skip: int = 0, limit: int = 100,
    ) -> list[ActivityLog]:
        query = db.query(ActivityLog).order_by(ActivityLog.id.desc())
        if user_id:
            query = query.filter(ActivityLog.user_id == user_id)
        if start_date:
            query = query.filter(ActivityLog.created_at >= start_date)
        if end_date:
            query = query.filter(ActivityLog.created_at <= end_date)
        return query.offset(skip).limit(limit).all()

    def count_filtered(self, db: Session, *, user_id=None, start_date=None, end_date=None) -> int:
        query = db.query(func.count(ActivityLog.id))
        if user_id:
            query = query.filter(ActivityLog.user_id == user_id)
        if start_date:
            query = query.filter(ActivityLog.created_at >= start_date)
        if end_date:
            query = query.filter(ActivityLog.created_at <= end_date)
        return query.scalar() or 0
