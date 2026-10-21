from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base


class AuditLogModel(Base):
    __mapper_args__ = {"batch": False}
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_company_entity", "company_id", "entity_type", "entity_id"),
        Index("ix_audit_logs_trace_id", "trace_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    actor_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    actor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(nullable=False)
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    payload_diff: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    previous_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    entry_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True)
    chain_sequence: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )


class LegalHold(Base):
    __tablename__ = "legal_holds"
    __table_args__ = (UniqueConstraint("company_id", "entity_type", "entity_id", name="uq_legal_hold_entity"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[UUID] = mapped_column(index=True)
    reason: Mapped[str] = mapped_column(Text)
    placed_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    lifted_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"))
    placed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    lifted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
