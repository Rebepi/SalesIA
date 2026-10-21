from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class QuotationModel(Base, TimestampMixin):
    __tablename__ = "quotations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    branch_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)
    customer_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    quotation_number: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    valid_until: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    delivery_terms: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    special_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    seller_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_channel: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    delivery_recipient: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    communication_log_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    converted_order_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    lines_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)


class OrderModel(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    branch_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    customer_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    warehouse_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)
    quotation_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    order_number: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="confirmed", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    stock_reserved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    delivery_terms: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_po_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    attachments_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    reservation_expires_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    lines_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    history_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    picking_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
