from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class InventoryLot(Base, TimestampMixin):
    __tablename__ = "inventory_lots"
    __table_args__ = (UniqueConstraint("company_id", "product_id", "lot_code", name="uq_lot_product_code"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    lot_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    supplier_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    manufacture_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expiration_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class InventorySerial(Base, TimestampMixin):
    __tablename__ = "inventory_serials"
    __table_args__ = (UniqueConstraint("company_id", "product_id", "serial_number", name="uq_serial_product_number"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    serial_number: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    warehouse_id: Mapped[UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    location_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("warehouse_locations.id", ondelete="SET NULL"), nullable=True
    )
    lot_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("inventory_lots.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="IN_STOCK", nullable=False)
    current_doc_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    current_doc_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)


class InventoryQuarantine(Base, TimestampMixin):
    __tablename__ = "inventory_quarantines"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="IN_QUARANTINE", nullable=False)
    reference_doc_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    reference_doc_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    inspected_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
