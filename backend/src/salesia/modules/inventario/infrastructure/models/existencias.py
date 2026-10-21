from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from salesia.modules.catalogo.infrastructure.models import ProductModel
    from salesia.modules.organizacion.infrastructure.models import WarehouseModel
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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from salesia.shared.infrastructure.database import Base, TimestampMixin


class InventoryStockModel(Base, TimestampMixin):
    __tablename__ = "inventory_stocks"
    __table_args__ = (
        UniqueConstraint("company_id", "warehouse_id", "product_id", name="uq_inventory_warehouse_product"),
        ForeignKeyConstraint(
            ["company_id", "warehouse_id"],
            ["warehouses.company_id", "warehouses.id"],
            name="fk_inventory_warehouse_scope",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "product_id"],
            ["products.company_id", "products.id"],
            name="fk_inventory_product_scope",
            ondelete="RESTRICT",
        ),
        CheckConstraint("physical_quantity >= 0", name="ck_stock_physical_non_negative"),
        CheckConstraint("reserved_quantity >= 0", name="ck_stock_reserved_non_negative"),
        CheckConstraint("physical_quantity >= reserved_quantity", name="ck_stock_physical_gte_reserved"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    product_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    average_cost: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"), nullable=False)
    physical_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)

    warehouse: Mapped["WarehouseModel"] = relationship("WarehouseModel", foreign_keys=[warehouse_id])
    product: Mapped["ProductModel"] = relationship("ProductModel", foreign_keys=[product_id])


class KardexMovementModel(Base, TimestampMixin):
    __tablename__ = "kardex_movements"
    __table_args__ = (
        ForeignKeyConstraint(
            ["company_id", "warehouse_id"],
            ["warehouses.company_id", "warehouses.id"],
            name="fk_kardex_warehouse_scope",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "product_id"],
            ["products.company_id", "products.id"],
            name="fk_kardex_product_scope",
            ondelete="RESTRICT",
        ),
        CheckConstraint("resulting_physical_qty >= 0", name="ck_kardex_resulting_qty_positive"),
        Index("ix_kardex_company_product_occurred", "company_id", "product_id", "occurred_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    product_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    movement_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reference_doc_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reference_doc_id: Mapped[UUID] = mapped_column(nullable=False)
    quantity_delta: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    resulting_physical_qty: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    moving_average_cost: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    warehouse: Mapped["WarehouseModel"] = relationship("WarehouseModel", foreign_keys=[warehouse_id])
    product: Mapped["ProductModel"] = relationship("ProductModel", foreign_keys=[product_id])


class WarehouseLocation(Base, TimestampMixin):
    __tablename__ = "warehouse_locations"
    __table_args__ = (UniqueConstraint("company_id", "warehouse_id", "code", name="uq_location_warehouse_code"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    aisle: Mapped[str] = mapped_column(String(32), default="A", nullable=False)
    rack: Mapped[str] = mapped_column(String(32), default="1", nullable=False)
    shelf: Mapped[str] = mapped_column(String(32), default="1", nullable=False)
    bin: Mapped[str] = mapped_column(String(32), default="1", nullable=False)
    capacity_units: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("1000.000000"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class LocationStock(Base, TimestampMixin):
    __tablename__ = "inventory_location_stocks"
    __table_args__ = (UniqueConstraint("company_id", "location_id", "product_id", name="uq_location_stock_product"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    location_id: Mapped[UUID] = mapped_column(
        ForeignKey("warehouse_locations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)


class StockRule(Base, TimestampMixin):
    __tablename__ = "inventory_stock_rules"
    __table_args__ = (UniqueConstraint("company_id", "warehouse_id", "product_id", name="uq_stock_rules_wh_prod"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    min_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    max_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    reorder_point: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    reorder_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class InventoryAlert(Base, TimestampMixin):
    __tablename__ = "inventory_alerts"
    __table_args__ = (UniqueConstraint("company_id", "dedup_hash", name="uq_inventory_alert_dedup"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), default="WARNING", nullable=False)
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    dedup_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    responsible_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class InventoryReservation(Base, TimestampMixin):
    __tablename__ = "inventory_reservations"
    __table_args__ = (
        UniqueConstraint("company_id", "document_type", "document_id", "product_id", name="uq_reservation_doc_prod"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(32), nullable=False)
    document_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class InventoryValuationSetting(Base, TimestampMixin):
    __tablename__ = "inventory_valuation_settings"
    __table_args__ = (UniqueConstraint("company_id", "product_id", name="uq_valuation_company_product"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=True)
    costing_method: Mapped[str] = mapped_column(String(32), default="AVERAGE_WEIGHTED", nullable=False)
    rounding_decimals: Mapped[int] = mapped_column(Integer, default=6, nullable=False)


class InventoryReconciliation(Base, TimestampMixin):
    __tablename__ = "inventory_reconciliations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    ledger_balance: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    cached_stock_balance: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    discrepancy_delta: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="DETECTED", nullable=False)
    before_balance: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    after_balance: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    repair_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    evidence: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    repaired_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    repaired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
