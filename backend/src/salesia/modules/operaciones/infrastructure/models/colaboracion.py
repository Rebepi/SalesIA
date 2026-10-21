from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base


class CollaborationComment(Base):
    __tablename__ = "collaboration_comments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    resource_type: Mapped[str] = mapped_column(String(64), index=True)
    resource_id: Mapped[UUID] = mapped_column(index=True)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    sanitized_content: Mapped[str] = mapped_column(Text)
    mentions_json: Mapped[str] = mapped_column(Text, default="[]")
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CollaborationTask(Base):
    __tablename__ = "collaboration_tasks"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assignee_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    creator_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    priority: Mapped[str] = mapped_column(String(32), default="normal")
    resource_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("collaboration_tasks.id", ondelete="RESTRICT"), nullable=True, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    checklist_json: Mapped[str] = mapped_column(Text, default="[]", server_default="[]", nullable=False)
    dependencies_json: Mapped[str] = mapped_column(Text, default="[]", server_default="[]", nullable=False)
    recurrence_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CollaborationApproval(Base):
    __tablename__ = "collaboration_approvals"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    resource_type: Mapped[str] = mapped_column(String(64), index=True)
    resource_id: Mapped[UUID] = mapped_column(index=True)
    document_version: Mapped[int] = mapped_column(Integer, default=1)
    policy_name: Mapped[str] = mapped_column(String(128))
    requested_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    decided_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    decision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    document_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    policy_snapshot_json: Mapped[str] = mapped_column(Text, default="{}", server_default="{}", nullable=False)
    stage_index: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class SavedView(Base):
    __tablename__ = "saved_views"
    __table_args__ = (UniqueConstraint("company_id", "user_id", "resource_type", "name", name="uq_user_saved_view"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    resource_type: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(128))
    schema_version: Mapped[int] = mapped_column(Integer, default=1)
    config_json: Mapped[str] = mapped_column(Text)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ContextualHelpArticle(Base):
    __tablename__ = "contextual_help_articles"
    __table_args__ = (UniqueConstraint("screen", "error_code", "role", "version", name="uq_help_article"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    screen: Mapped[str] = mapped_column(String(128), index=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(64), default="all")
    version: Mapped[str] = mapped_column(String(32), default="1.0")
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
