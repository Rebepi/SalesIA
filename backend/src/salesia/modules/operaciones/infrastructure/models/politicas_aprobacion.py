from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class ApprovalPolicyModel(Base, TimestampMixin):
    __tablename__ = "business_approval_policies"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_approval_policy_code"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    code: Mapped[str] = mapped_column(String(64))
    resource_type: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(32))
    config_json: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class ApprovalVoteModel(Base, TimestampMixin):
    __tablename__ = "business_approval_votes"
    __table_args__ = (UniqueConstraint("approval_id", "stage", "actor_id", name="uq_approval_vote_actor_stage"), UniqueConstraint("approval_id", "stage", "represented_principal_id", name="uq_approval_vote_principal_stage"))
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    approval_id: Mapped[UUID] = mapped_column(ForeignKey("collaboration_approvals.id"), index=True)
    stage: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    represented_principal_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(Text)


class DelegationModel(Base, TimestampMixin):
    __tablename__ = "business_approval_delegations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    principal_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    delegate_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str] = mapped_column(Text)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
