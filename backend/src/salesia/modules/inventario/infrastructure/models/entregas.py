from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class DeliveryShipment(Base, TimestampMixin):
    __tablename__ = "delivery_shipments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    delivery_document_id: Mapped[UUID] = mapped_column(
        ForeignKey("supply_documents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    sale_id: Mapped[UUID] = mapped_column(ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False, index=True)
    recipient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    delivery_address: Mapped[str] = mapped_column(String(500), nullable=False)
    recipient_phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    carrier: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    tracking_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    shipping_fee_charged: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    logistics_cost: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    estimated_delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_guaranteed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ready", nullable=False)
    dispatched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class DeliveryTrackingEvent(Base, TimestampMixin):
    __tablename__ = "delivery_tracking_events"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    delivery_id: Mapped[UUID] = mapped_column(
        ForeignKey("supply_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_code: Mapped[str] = mapped_column(String(64), nullable=False)
    event_status: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    dedup_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)


class ProofOfDelivery(Base, TimestampMixin):
    __tablename__ = "proof_of_deliveries"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    delivery_id: Mapped[UUID] = mapped_column(
        ForeignKey("supply_documents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    received_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    received_by_id_doc: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    delivered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    signature_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)


class DeliveryIncident(Base, TimestampMixin):
    __tablename__ = "delivery_incidents"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    delivery_id: Mapped[UUID] = mapped_column(
        ForeignKey("supply_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    incident_type: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    responsible_user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    rescheduled_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_status: Mapped[str] = mapped_column(String(32), default="OPEN", nullable=False)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
