from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base


class AnalyticsArtifact(Base):
    __tablename__ = "analytics_artifacts"
    __table_args__ = (
        UniqueConstraint("company_id", "kind", "artifact_key", "version", name="uq_analytics_artifact_version"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32), index=True)
    artifact_key: Mapped[str] = mapped_column(String(128), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="active")
    data_json: Mapped[str] = mapped_column(Text)
    parent_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("analytics_artifacts.id"))
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
