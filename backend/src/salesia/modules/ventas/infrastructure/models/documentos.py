from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from salesia.modules.catalogo.infrastructure.models import ProductModel
    from salesia.modules.clientes.infrastructure.models import CustomerModel
    from salesia.modules.organizacion.infrastructure.models import BranchModel
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from salesia.shared.infrastructure.database import Base, TimestampMixin


class SaleModel(Base, TimestampMixin):
    __tablename__ = "sales"
    __table_args__ = (
        UniqueConstraint("company_id", "id", name="uq_sales_company_id"),
        UniqueConstraint("company_id", "series", "number", name="uq_sales_series_number"),
        ForeignKeyConstraint(
            ["company_id", "branch_id"],
            ["branches.company_id", "branches.id"],
            name="fk_sales_branch_scope",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "customer_id"],
            ["customers.company_id", "customers.id"],
            name="fk_sales_customer_scope",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "status IN ('draft', 'confirmed', 'paid', 'cancelled', 'refunded')", name="ck_sales_valid_status"
        ),
        CheckConstraint("subtotal_amount >= 0", name="ck_sales_subtotal_positive"),
        CheckConstraint("tax_amount >= 0", name="ck_sales_tax_positive"),
        CheckConstraint("total_amount >= 0", name="ck_sales_total_positive"),
        CheckConstraint("paid_amount >= 0", name="ck_sales_paid_positive"),
        Index("ix_sales_company_status_created", "company_id", "status", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    branch_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    customer_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    sales_rep_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("sales_representatives.id"), nullable=True, index=True
    )
    warehouse_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_credit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    series: Mapped[str] = mapped_column(String(16), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("1.000000"), nullable=False)
    coupon_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delivery_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internal_observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pricing_explanation_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=30, server_default="30", nullable=False)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    order_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("orders.id", ondelete="RESTRICT"), nullable=True, index=True)
    fulfillment_status: Mapped[str] = mapped_column(String(32), default="pending", server_default="pending", nullable=False)
    commission_snapshot_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_calendar_snapshot_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    lines: Mapped[list["SaleLineModel"]] = relationship(
        "SaleLineModel", back_populates="sale", cascade="all, delete-orphan", passive_deletes=True
    )
    branch: Mapped["BranchModel"] = relationship("BranchModel", foreign_keys=[branch_id])
    customer: Mapped["CustomerModel"] = relationship("CustomerModel", foreign_keys=[customer_id])


class SaleLineModel(Base, TimestampMixin):
    __tablename__ = "sale_lines"
    __table_args__ = (
        UniqueConstraint("sale_id", "line_number", name="uq_sale_lines_line_number"),
        ForeignKeyConstraint(
            ["company_id", "sale_id"],
            ["sales.company_id", "sales.id"],
            name="fk_sale_lines_sale_scope",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["company_id", "product_id"],
            ["products.company_id", "products.id"],
            name="fk_sale_lines_product_scope",
            ondelete="RESTRICT",
        ),
        CheckConstraint("quantity > 0", name="ck_sale_lines_qty_strictly_positive"),
        CheckConstraint("unit_price_snapshot >= 0", name="ck_sale_lines_price_positive"),
        CheckConstraint("unit_cost_snapshot >= 0", name="ck_sale_lines_cost_positive"),
        CheckConstraint("discount_amount >= 0", name="ck_sale_lines_discount_positive"),
        CheckConstraint("tax_rate_snapshot >= 0", name="ck_sale_lines_tax_rate_positive"),
        CheckConstraint("subtotal_amount >= 0", name="ck_sale_lines_subtotal_positive"),
        CheckConstraint("tax_amount >= 0", name="ck_sale_lines_tax_positive"),
        CheckConstraint("total_amount >= 0", name="ck_sale_lines_total_positive"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sale_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    product_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    sku_snapshot: Mapped[str] = mapped_column(String(64), nullable=False)
    name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_of_measure_snapshot: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    unit_price_snapshot: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    unit_cost_snapshot: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    tax_rate_snapshot: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    serial_numbers_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    warranty_months_snapshot: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    warranty_policy_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    return_policy_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order_line_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fulfilled_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 6), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    sale: Mapped["SaleModel"] = relationship("SaleModel", back_populates="lines")
    product: Mapped["ProductModel"] = relationship("ProductModel", foreign_keys=[product_id])
