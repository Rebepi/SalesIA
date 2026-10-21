from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class CustomerModel(Base, TimestampMixin):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("company_id", "doc_type", "doc_number", name="uq_customers_doc"),
        UniqueConstraint("company_id", "id", name="uq_customers_company_id"),
        CheckConstraint("credit_limit >= 0", name="ck_customers_credit_limit_positive"),
        CheckConstraint("current_balance >= 0", name="ck_customers_current_balance_positive"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(16), nullable=False)
    doc_number: Mapped[str] = mapped_column(String(32), nullable=False)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    current_balance: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CustomerProfileModel(Base, TimestampMixin):
    __tablename__ = "customer_profiles"
    __table_args__ = (UniqueConstraint("company_id", "customer_id", name="uq_customer_profile_scope"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    assigned_sales_rep_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)
    sales_team: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    backup_sales_rep_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    price_list_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    preferred_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    is_credit_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    credit_block_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    credit_block_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tags_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    assignment_history_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class CustomerContactModel(Base, TimestampMixin):
    __tablename__ = "customer_contacts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(128), default="Contacto", nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preferences_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    purpose: Mapped[str] = mapped_column(String(32), default="general", server_default="general", nullable=False)
    valid_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    can_purchase: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    can_receive: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)


class CustomerAddressModel(Base, TimestampMixin):
    __tablename__ = "customer_addresses"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    address_type: Mapped[str] = mapped_column(String(32), default="comercial", nullable=False)
    street: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(128), default="Lima", nullable=False)
    state: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    country: Mapped[str] = mapped_column(String(64), default="PE", nullable=False)
    postal_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    valid_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)


class CustomerNoteModel(Base, TimestampMixin):
    __tablename__ = "customer_notes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    author_email: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(32), default="comercial", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    attachments_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)


class CustomerOpportunityModel(Base, TimestampMixin):
    __tablename__ = "customer_opportunities"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    stage: Mapped[str] = mapped_column(String(32), default="lead", nullable=False)
    estimated_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    probability: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("50.00"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    assigned_to_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)
    next_action: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    next_action_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    loss_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    converted_quotation_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    stage_history_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)


class CustomerActivityModel(Base, TimestampMixin):
    __tablename__ = "customer_activities"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    activity_type: Mapped[str] = mapped_column(String(32), default="call", nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reminder_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assigned_to_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class CustomerLoyaltyLedgerModel(Base):
    __tablename__ = "customer_loyalty_ledger"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    movement_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reference_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class CustomerSegmentModel(Base, TimestampMixin):
    __tablename__ = "customer_segments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criteria_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CustomerImportBatchModel(Base):
    __tablename__ = "customer_import_batches"
    __table_args__ = (UniqueConstraint("company_id", "batch_key", name="uq_customer_import_batch"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    batch_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
