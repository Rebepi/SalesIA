from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class ReceivableScheduleModel(Base, TimestampMixin):
    __tablename__ = "receivable_schedules"
    __table_args__ = (UniqueConstraint("company_id", "sale_id", name="uq_receivable_schedule_sale"), CheckConstraint("opening_balance > 0", name="ck_receivable_schedule_balance"))
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    sale_id: Mapped[UUID] = mapped_column(ForeignKey("sales.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    active_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    schedule_json: Mapped[str] = mapped_column(Text, default="[]")
    history_json: Mapped[str] = mapped_column(Text, default="[]")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))


class ReceivableInstallmentAllocationModel(Base, TimestampMixin):
    __tablename__ = "receivable_installment_allocations"
    __table_args__ = (UniqueConstraint("allocation_id", "schedule_id", "schedule_version", "installment_id", name="uq_receivable_installment_allocation"), CheckConstraint("amount > 0", name="ck_receivable_installment_allocation_amount"))
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    allocation_id: Mapped[UUID] = mapped_column(ForeignKey("payment_allocations.id"), index=True)
    schedule_id: Mapped[UUID] = mapped_column(ForeignKey("receivable_schedules.id"), index=True)
    schedule_version: Mapped[int] = mapped_column(Integer)
    installment_id: Mapped[UUID] = mapped_column(index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
