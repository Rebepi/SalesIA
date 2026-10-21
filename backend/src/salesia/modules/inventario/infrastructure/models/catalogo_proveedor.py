from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class SupplierProductModel(Base, TimestampMixin):
    __tablename__ = "supplier_products"
    __table_args__ = (
        UniqueConstraint("company_id", "supplier_id", "product_id", "currency", name="uq_supplier_product_currency"),
        CheckConstraint("unit_cost >= 0 AND minimum_quantity > 0 AND order_multiple > 0 AND lead_time_days >= 0", name="ck_supplier_product_values"),
        CheckConstraint("valid_until IS NULL OR valid_from IS NULL OR valid_until >= valid_from", name="ck_supplier_product_dates"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    supplier_id: Mapped[UUID] = mapped_column(ForeignKey("suppliers.id"), index=True)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"), index=True)
    purchase_presentation: Mapped[str] = mapped_column(String(128), default="")
    supplier_sku: Mapped[str] = mapped_column(String(128), default="")
    currency: Mapped[str] = mapped_column(String(3))
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    minimum_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("1"))
    order_multiple: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("1"))
    lead_time_days: Mapped[int] = mapped_column(Integer, default=7)
    valid_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_preferred: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    notes: Mapped[str] = mapped_column(Text, default="")
