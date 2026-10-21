from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class PaymentModel(Base, TimestampMixin):
    __tablename__ = "payments"
    __table_args__ = (
        ForeignKeyConstraint(
            ["company_id", "sale_id"],
            ["sales.company_id", "sales.id"],
            name="fk_payments_sale_scope",
            ondelete="RESTRICT",
        ),
        CheckConstraint("amount > 0", name="ck_payments_amount_strictly_positive"),
        CheckConstraint("status IN ('pending', 'confirmed', 'failed', 'refunded')", name="ck_payments_valid_status"),
        Index("ix_payments_company_sale", "company_id", "sale_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sale_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    payment_method: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    reference_code: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="confirmed", nullable=False)


class PaymentMethodConfigModel(Base, TimestampMixin):
    __tablename__ = "payment_methods"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_payment_methods_company_code"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_reference: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_cash_session: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allowed_currencies: Mapped[str] = mapped_column(String(128), default="USD,PEN,EUR", nullable=False)


class PaymentAllocationModel(Base, TimestampMixin):
    __tablename__ = "payment_allocations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    payment_id: Mapped[UUID] = mapped_column(ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False, index=True)
    sale_id: Mapped[UUID] = mapped_column(ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False, index=True)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)


class PaymentIntentModel(Base, TimestampMixin):
    __tablename__ = "payment_intents"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sale_id: Mapped[UUID] = mapped_column(ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    provider_intent_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    client_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class FinanceReconciliationModel(Base, TimestampMixin):
    __tablename__ = "finance_reconciliations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)
    total_matched: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    total_discrepancy: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(nullable=True)


class FinanceReconciliationItemModel(Base, TimestampMixin):
    __tablename__ = "finance_reconciliation_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    reconciliation_id: Mapped[UUID] = mapped_column(
        ForeignKey("finance_reconciliations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    classification: Mapped[str] = mapped_column(String(32), nullable=False)
    payment_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    external_reference: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    local_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 6), nullable=True)
    external_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 6), nullable=True)
    difference_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 6), nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_by: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    resolution_action: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class PaymentDisputeModel(Base, TimestampMixin):
    __tablename__ = "payment_disputes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    payment_id: Mapped[UUID] = mapped_column(ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False, index=True)
    sale_id: Mapped[UUID] = mapped_column(ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    deadline_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="under_review", nullable=False)


class PaymentReversalModel(Base, TimestampMixin):
    __tablename__ = "payment_reversals"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    payment_id: Mapped[UUID] = mapped_column(ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False, index=True)
    sale_id: Mapped[UUID] = mapped_column(ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_code: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    reversed_by: Mapped[Optional[UUID]] = mapped_column(nullable=True)


class TransferProofModel(Base, TimestampMixin):
    __tablename__ = "transfer_proofs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    payment_id: Mapped[UUID] = mapped_column(ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False, index=True)
    document_url: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_code: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_by: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
