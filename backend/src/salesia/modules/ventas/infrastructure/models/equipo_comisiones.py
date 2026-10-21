from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class SalesRepresentative(Base):
    __tablename__ = "sales_representatives"
    __table_args__ = (UniqueConstraint("company_id", "user_id", name="uq_sales_representative_user"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    user_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    branch_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("branches.id"), nullable=True)
    team: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    supervisor_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255))
    territory: Mapped[str] = mapped_column(String(128))
    monthly_quota: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SalesTarget(Base):
    __tablename__ = "sales_targets"
    __table_args__ = (
        UniqueConstraint("company_id", "representative_id", "period", "target_type", "currency", "scope", name="uq_sales_target_currency_scope"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    representative_id: Mapped[UUID] = mapped_column(ForeignKey("sales_representatives.id"), index=True)
    period: Mapped[str] = mapped_column(String(7))
    target_type: Mapped[str] = mapped_column(String(32), default="amount")
    target_value: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    scope: Mapped[str] = mapped_column(String(32), default="individual")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CommissionSettlement(Base):
    __tablename__ = "commission_settlements"
    __table_args__ = (
        UniqueConstraint("company_id", "representative_id", "period", "currency", name="uq_commission_settlement_currency_period"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    representative_id: Mapped[UUID] = mapped_column(ForeignKey("sales_representatives.id"), index=True)
    period: Mapped[str] = mapped_column(String(7))
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    history_json: Mapped[str] = mapped_column(Text, default="[]", server_default="[]", nullable=False)
    calculation_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    payout_reference: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    gross_sales: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    returns_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    net_sales: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    target_quota: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(10, 6))
    commission_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    payable_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"), nullable=False)
    carried_balance: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="calculated")
    approved_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"))
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rules_version: Mapped[int] = mapped_column(Integer, default=1)
    rules_snapshot_json: Mapped[str] = mapped_column(Text, default="{}", server_default="{}", nullable=False)
    calculation_detail_json: Mapped[str] = mapped_column(Text, default="[]", server_default="[]", nullable=False)
    prior_adjustments: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"))
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CommissionEntryModel(Base, TimestampMixin):
    __tablename__ = "commission_entries"
    __table_args__ = (UniqueConstraint("settlement_id", "sale_id", name="uq_commission_entry_sale"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    settlement_id: Mapped[UUID] = mapped_column(ForeignKey("commission_settlements.id", ondelete="RESTRICT"), nullable=False, index=True)
    sale_id: Mapped[UUID] = mapped_column(ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    earned_base: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    cumulative_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    details_json: Mapped[str] = mapped_column(Text, nullable=False)


class CommissionObservationModel(Base, TimestampMixin):
    __tablename__ = "commission_observations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    settlement_id: Mapped[UUID] = mapped_column(ForeignKey("commission_settlements.id", ondelete="RESTRICT"), nullable=False, index=True)
    sale_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("sales.id", ondelete="RESTRICT"), nullable=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    resolved_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
