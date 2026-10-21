from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from salesia.shared.infrastructure.database import Base, TimestampMixin


class PhysicalCountSession(Base, TimestampMixin):
    __tablename__ = "physical_count_sessions"
    __table_args__ = (UniqueConstraint("company_id", "id", name="uq_count_session_company_id"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    count_code: Mapped[str] = mapped_column(String(32), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), default="FULL", nullable=False)
    scope_filter: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    cutoff_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    is_blind: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending_count", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    approved_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    lines: Mapped[list["PhysicalCountLine"]] = relationship(cascade="all, delete-orphan", back_populates="session")


class PhysicalCountLine(Base, TimestampMixin):
    __tablename__ = "physical_count_lines"
    __table_args__ = (UniqueConstraint("session_id", "product_id", name="uq_count_session_product"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("physical_count_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    system_quantity_snapshot: Mapped[Decimal] = mapped_column(
        Numeric(20, 6), default=Decimal("0.000000"), nullable=False
    )
    counted_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    counted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    difference_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    session: Mapped["PhysicalCountSession"] = relationship(back_populates="lines")


class InventoryPickingList(Base, TimestampMixin):
    __tablename__ = "inventory_picking_lists"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sale_id: Mapped[UUID] = mapped_column(ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False, index=True)
    assigned_to: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    lines: Mapped[list["InventoryPickingLine"]] = relationship(
        cascade="all, delete-orphan", back_populates="picking_list"
    )


class InventoryPickingLine(Base, TimestampMixin):
    __tablename__ = "inventory_picking_lines"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    picking_list_id: Mapped[UUID] = mapped_column(
        ForeignKey("inventory_picking_lists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    location_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("warehouse_locations.id", ondelete="SET NULL"), nullable=True
    )
    lot_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("inventory_lots.id", ondelete="SET NULL"), nullable=True)
    expected_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    picked_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    picking_list: Mapped["InventoryPickingList"] = relationship(back_populates="lines")
