from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class TaskRecurrenceModel(Base, TimestampMixin):
    __tablename__ = "task_recurrences"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    template_json: Mapped[str] = mapped_column(Text)
    schedule_json: Mapped[str] = mapped_column(Text)
    next_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class TaskOccurrenceModel(Base):
    __tablename__ = "task_occurrences"
    __table_args__ = (UniqueConstraint("recurrence_id", "due_at", name="uq_task_occurrence_due"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    recurrence_id: Mapped[UUID] = mapped_column(ForeignKey("task_recurrences.id"), index=True)
    task_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("collaboration_tasks.id"), nullable=True)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="created")
