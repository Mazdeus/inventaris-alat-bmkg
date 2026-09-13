"""ActivityLogRepository — query read-only untuk activity_logs."""
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.models.user import User
from app.repositories.base import BaseRepository


class ActivityLogRepository(BaseRepository[ActivityLog]):
    def __init__(self):
        super().__init__(ActivityLog)

    def _apply_filters(
        self,
        query,
        *,
        user_id: int | None = None,
        start_date=None,
        end_date=None,
        search: str | None = None,
    ):
        if user_id:
            query = query.filter(ActivityLog.user_id == user_id)
        if start_date:
            query = query.filter(ActivityLog.created_at >= start_date)
        if end_date:
            query = query.filter(ActivityLog.created_at <= end_date)
        if search and search.strip():
            s = f"%{search.strip()}%"
            query = query.outerjoin(User, ActivityLog.user_id == User.id).filter(
                or_(
                    ActivityLog.activity.ilike(s),
                    ActivityLog.reference_table.ilike(s),
                    ActivityLog.ip_address.ilike(s),
                    User.full_name.ilike(s),
                    User.username.ilike(s),
                )
            )
        return query

    def get_filtered(
        self, db: Session, *,
        user_id: int | None = None,
        start_date=None, end_date=None,
        search: str | None = None,
        skip: int = 0, limit: int = 100,
    ) -> list[ActivityLog]:
        query = db.query(ActivityLog)
        query = self._apply_filters(query, user_id=user_id, start_date=start_date, end_date=end_date, search=search)
        return query.order_by(ActivityLog.id.desc()).offset(skip).limit(limit).all()

    def count_filtered(
        self, db: Session, *,
        user_id: int | None = None,
        start_date=None, end_date=None,
        search: str | None = None,
    ) -> int:
        query = db.query(func.count(ActivityLog.id))
        query = self._apply_filters(query, user_id=user_id, start_date=start_date, end_date=end_date, search=search)
        return query.scalar() or 0
