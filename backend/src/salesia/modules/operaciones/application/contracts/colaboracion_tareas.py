from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TaskChecklistItem(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    done: bool = False


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)

    description: Optional[str] = Field(default=None, max_length=2000)

    assignee_id: Optional[UUID] = None

    due_date: Optional[datetime] = None

    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")

    resource_type: Optional[str] = None

    resource_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None
    checklist: list[TaskChecklistItem] = Field(default_factory=list, max_length=100)
    dependencies: list[UUID] = Field(default_factory=list, max_length=100)


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)

    description: Optional[str] = Field(default=None, max_length=2000)

    due_date: Optional[datetime] = None

    status: Optional[str] = Field(default=None, pattern="^(pending|in_progress|completed|cancelled)$")

    assignee_id: Optional[UUID] = None

    priority: Optional[str] = Field(default=None, pattern="^(low|normal|high|urgent)$")

    resolution_notes: Optional[str] = None

    resource_type: Optional[str] = None

    resource_id: Optional[UUID] = None
    version: Optional[int] = Field(default=None, ge=1)
    checklist: Optional[list[TaskChecklistItem]] = Field(default=None, max_length=100)
    dependencies: Optional[list[UUID]] = Field(default=None, max_length=100)
