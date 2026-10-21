from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from salesia.shared.infrastructure.database import Base, TimestampMixin


class CreditNoteModel(Base, TimestampMixin):
    __tablename__ = "credit_notes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    branch_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sale_id: Mapped[UUID] = mapped_column(ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False, index=True)
    return_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)
    series: Mapped[str] = mapped_column(String(16), nullable=False)
    number: Mapped[int] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(32), default="02_DEVOLUCION", nullable=False)
    reason_description: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="issued", nullable=False)
    issued_by: Mapped[Optional[UUID]] = mapped_column(nullable=True)

    lines: Mapped[list["CreditNoteLineModel"]] = relationship(
        "CreditNoteLineModel", back_populates="credit_note", cascade="all, delete-orphan"
    )


class CreditNoteLineModel(Base, TimestampMixin):
    __tablename__ = "credit_note_lines"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    credit_note_id: Mapped[UUID] = mapped_column(
        ForeignKey("credit_notes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sale_line_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    line_number: Mapped[int] = mapped_column(nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0.1800"), nullable=False)
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)

    credit_note: Mapped["CreditNoteModel"] = relationship("CreditNoteModel", back_populates="lines")


class CustomerCreditMovementModel(Base, TimestampMixin):
    __tablename__ = "customer_credit_movements"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    movement_type: Mapped[str] = mapped_column(String(32), nullable=False)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True, index=True)
    payment_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("payments.id", ondelete="RESTRICT"), nullable=True, index=True)
    amount_delta: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    resulting_balance: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reference_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class CustomerCreditAllocationModel(Base, TimestampMixin):
    __tablename__ = "customer_credit_allocations"
    __table_args__ = (
        UniqueConstraint("debit_id", "credit_id", name="uq_customer_credit_allocation_pair"),
        CheckConstraint("amount > 0", name="customer_credit_allocation_amount"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True)
    debit_id: Mapped[UUID] = mapped_column(ForeignKey("customer_credit_movements.id", ondelete="RESTRICT"), nullable=False, index=True)
    credit_id: Mapped[UUID] = mapped_column(ForeignKey("customer_credit_movements.id", ondelete="RESTRICT"), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)


class CustomerCreditReservationModel(Base, TimestampMixin):
    __tablename__ = "customer_credit_reservations"
    __table_args__ = (CheckConstraint("amount >= 0", name="customer_credit_reservation_amount"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True)
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    sale_id: Mapped[UUID] = mapped_column(ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False, index=True)
    payment_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("payments.id", ondelete="RESTRICT"), nullable=True, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    sources_json: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    version: Mapped[int] = mapped_column(nullable=False, default=1)


class CustomerCreditConversionModel(Base, TimestampMixin):
    __tablename__ = "customer_credit_conversions"
    __table_args__ = (
        CheckConstraint("source_amount > 0 AND target_amount > 0 AND rate > 0", name="customer_credit_conversion_amounts"),
        CheckConstraint("source_currency <> target_currency", name="customer_credit_conversion_currencies"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True)
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    source_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    target_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    source_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    rate_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    source_ids_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    review_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    debit_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("customer_credit_movements.id", ondelete="RESTRICT"), nullable=True)
    credit_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("customer_credit_movements.id", ondelete="RESTRICT"), nullable=True)
    version: Mapped[int] = mapped_column(nullable=False, default=1)


class ReturnModel(Base, TimestampMixin):
    __tablename__ = "sales_returns"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sale_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("sales.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(32), default="requested", nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    is_without_receipt: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    manual_valuation_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 6), nullable=True)
    authorized_exception: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exception_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    requested_by: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    approved_by: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    rejection_criterion: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    evidence_urls_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    credit_note_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)
    exchange_sale_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    details_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    lines: Mapped[list["ReturnLineModel"]] = relationship(
        "ReturnLineModel", back_populates="return_doc", cascade="all, delete-orphan"
    )


class ReturnLineModel(Base, TimestampMixin):
    __tablename__ = "sales_return_lines"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    return_id: Mapped[UUID] = mapped_column(
        ForeignKey("sales_returns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    unit_price_snapshot: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    unit_cost_snapshot: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    discount_per_unit: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    tax_rate_snapshot: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0.1800"), nullable=False)
    disposition: Mapped[str] = mapped_column(String(32), default="RESTOCK", nullable=False)
    sale_line_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("sale_lines.id", ondelete="RESTRICT"), nullable=True, index=True)
    serial_numbers_json: Mapped[str] = mapped_column(Text, default="[]", server_default="[]", nullable=False)

    return_doc: Mapped["ReturnModel"] = relationship("ReturnModel", back_populates="lines")
