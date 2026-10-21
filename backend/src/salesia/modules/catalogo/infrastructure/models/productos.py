from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class ProductModel(Base, TimestampMixin):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("company_id", "sku", name="uq_products_company_sku"),
        UniqueConstraint("company_id", "id", name="uq_products_company_id"),
        CheckConstraint("unit_price >= 0", name="ck_products_unit_price_non_negative"),
        CheckConstraint("unit_cost >= 0", name="ck_products_unit_cost_non_negative"),
        CheckConstraint("tax_rate >= 0", name="ck_products_tax_rate_non_negative"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(16), default="NIU", nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0.1800"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ProductProfileModel(Base, TimestampMixin):
    __tablename__ = "product_profiles"
    __table_args__ = (UniqueConstraint("company_id", "product_id", name="uq_product_profiles_product"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    product_type: Mapped[str] = mapped_column(String(32), default="product", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    track_inventory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    category_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    warranty_period_months: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warranty_policy: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_kit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    price_includes_tax: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supplier_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    brand: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    length_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 3), nullable=True)
    width_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 3), nullable=True)
    height_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 3), nullable=True)
    weight_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 3), nullable=True)
    tracking_mode: Mapped[str] = mapped_column(String(16), default="NONE", nullable=False)


class ProductVariantModel(Base, TimestampMixin):
    __tablename__ = "product_variants"
    __table_args__ = (UniqueConstraint("company_id", "sku", name="uq_product_variants_sku"), UniqueConstraint("operational_product_id", name="uq_variant_operational_product"))

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    attributes_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    price_delta: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    operational_product_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=True)


class ProductBarcodeModel(Base, TimestampMixin):
    __tablename__ = "product_barcodes"
    __table_args__ = (UniqueConstraint("company_id", "barcode", name="uq_product_barcodes_company_code"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True
    )
    barcode: Mapped[str] = mapped_column(String(64), nullable=False)
    barcode_type: Mapped[str] = mapped_column(String(32), default="EAN13", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ProductAttachmentModel(Base, TimestampMixin):
    __tablename__ = "product_attachments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ProductKitItemModel(Base, TimestampMixin):
    __tablename__ = "product_kit_items"
    __table_args__ = (UniqueConstraint("kit_product_id", "component_product_id", name="uq_kit_component"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    kit_product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    component_product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("1.000000"), nullable=False)


class ProductWarrantyClaimModel(Base, TimestampMixin):
    __tablename__ = "product_warranty_claims"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sale_id: Mapped[UUID] = mapped_column(ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    claim_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    warranty_period_months_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    issue_description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)
    sale_line_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("sale_lines.id"), nullable=True, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("1"), server_default="1", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    warranty_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_to: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    diagnosis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    policy_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    history_json: Mapped[str] = mapped_column(Text, default="[]", server_default="[]", nullable=False)
