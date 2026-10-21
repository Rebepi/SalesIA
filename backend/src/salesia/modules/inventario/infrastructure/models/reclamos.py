from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class SupplierClaimModel(Base, TimestampMixin):
    __tablename__ = "supplier_claims"
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_supplier_claim_code"),
        CheckConstraint("expected_amount >= 0 AND (agreed_amount IS NULL OR agreed_amount >= 0)", name="ck_supplier_claim_amounts"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    supplier_id: Mapped[UUID] = mapped_column(ForeignKey("suppliers.id"), index=True)
    purchase_order_id: Mapped[UUID] = mapped_column(ForeignKey("supply_documents.id"), index=True)
    code: Mapped[str] = mapped_column(String(32))
    source_kind: Mapped[str] = mapped_column(String(32))
    source_id: Mapped[UUID] = mapped_column(index=True)
    reason_type: Mapped[str] = mapped_column(String(32))
    resolution: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(Text)
    currency: Mapped[str] = mapped_column(String(3))
    expected_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    agreed_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 6), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="open")
    version: Mapped[int] = mapped_column(Integer, default=1)
    items_json: Mapped[str] = mapped_column(Text, default="[]")
    history_json: Mapped[str] = mapped_column(Text, default="[]")
    requested_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    acknowledged_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
