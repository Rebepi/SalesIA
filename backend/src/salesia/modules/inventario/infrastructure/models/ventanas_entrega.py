from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class DeliveryWindowModel(Base, TimestampMixin):
    __tablename__ = "delivery_windows"
    __table_args__ = (CheckConstraint("capacity > 0 AND ends_at > starts_at", name="ck_delivery_window_capacity_dates"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    branch_id: Mapped[UUID] = mapped_column(ForeignKey("branches.id"), index=True)
    mode: Mapped[str] = mapped_column(String(16))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    capacity: Mapped[int] = mapped_column(Integer)
    requirements: Mapped[str] = mapped_column(Text, default="")
    identity_required: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    history_json: Mapped[str] = mapped_column(Text, default="[]")
    calendar_snapshot_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))


class DeliveryWindowReservationModel(Base, TimestampMixin):
    __tablename__ = "delivery_window_reservations"
    __table_args__ = (UniqueConstraint("company_id", "delivery_id", name="uq_delivery_window_reservation"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    delivery_id: Mapped[UUID] = mapped_column(ForeignKey("supply_documents.id"), index=True)
    window_id: Mapped[UUID] = mapped_column(ForeignKey("delivery_windows.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="booked")
    version: Mapped[int] = mapped_column(Integer, default=1)
    authorized_people_json: Mapped[str] = mapped_column(Text, default="[]")
    requirements_snapshot: Mapped[str] = mapped_column(Text, default="")
    identity_required: Mapped[bool] = mapped_column(Boolean, default=False)
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    checked_in_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    checked_in_doc: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    history_json: Mapped[str] = mapped_column(Text, default="[]")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
