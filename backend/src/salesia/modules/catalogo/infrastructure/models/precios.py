from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class PriceListModel(Base, TimestampMixin):
    __tablename__ = "price_lists"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_price_lists_company_code"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    target_type: Mapped[str] = mapped_column(String(32), default="all", nullable=False)
    target_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PriceListItemModel(Base, TimestampMixin):
    __tablename__ = "price_list_items"
    __table_args__ = (UniqueConstraint("price_list_id", "product_id", "variant_id", name="uq_price_list_items_scope"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    price_list_id: Mapped[UUID] = mapped_column(
        ForeignKey("price_lists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True
    )
    fixed_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 6), nullable=True)
    discount_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)


class ProductVolumeTierModel(Base, TimestampMixin):
    __tablename__ = "product_volume_tiers"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    min_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 6), nullable=True)
    discount_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)


class PromotionModel(Base, TimestampMixin):
    __tablename__ = "promotions"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_promotions_company_code"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    is_exclusive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    product_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=True)
    min_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("1.000000"), nullable=False)
    discount_percentage: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    max_quota: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    current_uses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CouponModel(Base, TimestampMixin):
    __tablename__ = "coupons"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_coupons_company_code"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    discount_type: Mapped[str] = mapped_column(String(16), default="PERCENTAGE", nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    min_purchase_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_uses: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    current_uses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ProductPriceHistoryModel(Base, TimestampMixin):
    __tablename__ = "product_price_history"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    old_price: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    new_price: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    effective_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    changed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    batch_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
