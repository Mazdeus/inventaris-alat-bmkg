"""Schema ActivityLog — response untuk log aktivitas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: Optional[str] = ""


class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user: Optional[UserBrief] = None
    activity: str
    reference_table: Optional[str] = None
    reference_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    extra_data: Optional[str] = None
    created_at: datetime
