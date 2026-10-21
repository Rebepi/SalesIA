from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from salesia.shared.infrastructure.database import Base, TimestampMixin


class Supplier(Base):
    __tablename__ = "suppliers"
    __table_args__ = (UniqueConstraint("company_id", "tax_id"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    tax_id: Mapped[str] = mapped_column(String(32))
    legal_name: Mapped[str] = mapped_column(String(255))
    contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    bank_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    bank_account: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    qualification_status: Mapped[str] = mapped_column(String(32), default="approved", server_default="approved", nullable=False)
    qualification_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    qualification_history_json: Mapped[str] = mapped_column(Text, default="[]", server_default="[]", nullable=False)
    qualification_documents_json: Mapped[str] = mapped_column(Text, default="[]", server_default="[]", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)


class SupplyDocument(Base):
    __tablename__ = "supply_documents"
    __table_args__ = (UniqueConstraint("company_id", "id"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32))
    version: Mapped[int] = mapped_column(Integer, default=1)
    warehouse_id: Mapped[UUID] = mapped_column(ForeignKey("warehouses.id"))
    source_warehouse_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("warehouses.id"))
    supplier_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("suppliers.id"))
    supplier_claim_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("supplier_claims.id"), nullable=True, index=True)
    sale_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("sales.id"), index=True)
    parent_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("supply_documents.id"), index=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    lines: Mapped[list["SupplyLine"]] = relationship(cascade="all, delete-orphan")


class SupplyLine(Base):
    __tablename__ = "supply_lines"
    __table_args__ = (
        ForeignKeyConstraint(["company_id", "document_id"], ["supply_documents.company_id", "supply_documents.id"]),
        ForeignKeyConstraint(["company_id", "product_id"], ["products.company_id", "products.id"]),
        UniqueConstraint("document_id", "product_id"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    document_id: Mapped[UUID] = mapped_column(index=True)
    product_id: Mapped[UUID] = mapped_column(index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    processed_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"))
    cancelled_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"), server_default="0", nullable=False)
    damaged_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"))
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(20, 6))


class LandedCostAdjustment(Base, TimestampMixin):
    __tablename__ = "landed_cost_adjustments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    goods_receipt_id: Mapped[UUID] = mapped_column(
        ForeignKey("supply_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    charge_type: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    allocation_method: Mapped[str] = mapped_column(String(32), default="VALUE", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)


class PurchaseInvoiceMatch(Base, TimestampMixin):
    __tablename__ = "purchase_invoice_matches"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    purchase_order_id: Mapped[UUID] = mapped_column(
        ForeignKey("supply_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    goods_receipt_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("supply_documents.id", ondelete="SET NULL"), nullable=True
    )
    invoice_number: Mapped[str] = mapped_column(String(64), nullable=False)
    invoice_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    matched_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    discrepancy_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="UNDER_REVIEW", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    lines_snapshot_json: Mapped[str] = mapped_column(Text, default="[]", server_default="[]", nullable=False)
    validation_json: Mapped[str] = mapped_column(Text, default="{}", server_default="{}", nullable=False)
    policy_snapshot_json: Mapped[str] = mapped_column(Text, default="{}", server_default="{}", nullable=False)
