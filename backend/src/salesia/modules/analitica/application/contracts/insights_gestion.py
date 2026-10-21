from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class InsightStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(new|pending|read|in_review|acknowledged|resolved|actioned|dismissed|expired)$")

    reason: Optional[str] = None

    version: Optional[int] = None


class InsightBulkActionRequest(BaseModel):
    ids: list[UUID] = Field(min_length=1, max_length=100)

    action: str = Field(pattern="^(read|dismiss|resolve|snooze|task)$")

    assignee_id: Optional[UUID] = None

    due_date: Optional[datetime] = None

    snoozed_until: Optional[datetime] = None

    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")

    notes: str = Field(default="", max_length=2000)


class InsightFeedbackRequest(BaseModel):
    helpful: bool

    comment: Optional[str] = None

    reason: Optional[str] = None
