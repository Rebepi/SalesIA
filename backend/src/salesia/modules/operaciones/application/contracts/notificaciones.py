from typing import Optional

from pydantic import BaseModel, Field


class NotificationPreferenceRequest(BaseModel):
    category: str = Field(pattern="^(commercial|marketing|operations|security)$")

    channel: str = Field(default="in_app", pattern="^(in_app|email)$")

    enabled: bool

    schedule_start: Optional[str] = None

    schedule_end: Optional[str] = None


class NotificationReadRequest(BaseModel):
    read: bool = True
