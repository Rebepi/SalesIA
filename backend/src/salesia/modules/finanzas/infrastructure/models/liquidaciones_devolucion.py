from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class ReturnSettlementMovementModel(Base, TimestampMixin):
    __tablename__ = "return_settlement_movements"
    __table_args__ = (UniqueConstraint("company_id", "kind", "reference_id", name="uq_return_settlement_reference"), CheckConstraint("amount > 0", name="ck_return_settlement_amount"))
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    return_id: Mapped[UUID] = mapped_column(ForeignKey("sales_returns.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32))
    reference_id: Mapped[UUID] = mapped_column(index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    currency: Mapped[str] = mapped_column(String(3))
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
