"""ActivityLogService — pencatatan aktivitas pengguna ke log. (FR-28)"""
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog


class ActivityLogService:
    def log(
        self, db: Session, *,
        user_id: int | None = None, activity: str,
        reference_table: str | None = None,
        reference_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        extra_data: str | None = None,
    ) -> ActivityLog:
        log_entry = ActivityLog(
            user_id=user_id,
            activity=activity,
            reference_table=reference_table,
            reference_id=reference_id,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=extra_data,
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry
