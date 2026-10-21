from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class DeliveryVehicleModel(Base, TimestampMixin):
    __tablename__ = "delivery_vehicles"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_delivery_vehicle_code"), CheckConstraint("max_weight_kg > 0 AND max_volume_m3 > 0", name="ck_delivery_vehicle_capacity"))
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255))
    max_weight_kg: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    max_volume_m3: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class DeliveryRouteModel(Base, TimestampMixin):
    __tablename__ = "delivery_routes"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_delivery_route_code"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    code: Mapped[str] = mapped_column(String(32))
    service_date: Mapped[date] = mapped_column(Date, index=True)
    zone: Mapped[str] = mapped_column(String(128))
    vehicle_id: Mapped[UUID] = mapped_column(ForeignKey("delivery_vehicles.id"), index=True)
    responsible_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    warehouse_id: Mapped[UUID] = mapped_column(ForeignKey("warehouses.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)
    stops_json: Mapped[str] = mapped_column(Text, default="[]")
    history_json: Mapped[str] = mapped_column(Text, default="[]")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
