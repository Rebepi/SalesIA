from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class PettyCashFundModel(Base, TimestampMixin):
    __tablename__ = "petty_cash_funds"
    __table_args__ = (UniqueConstraint("company_id", "account_id", name="uq_petty_cash_account"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("cash_custody_accounts.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    policy_json: Mapped[str] = mapped_column(Text)
    history_json: Mapped[str] = mapped_column(Text, default="[]")


class PettyCashAdvanceModel(Base, TimestampMixin):
    __tablename__ = "petty_cash_advances"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_petty_cash_advance_code"), CheckConstraint("amount > 0", name="ck_petty_cash_advance_positive"))
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    fund_id: Mapped[UUID] = mapped_column(ForeignKey("petty_cash_funds.id"), index=True)
    beneficiary_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    code: Mapped[str] = mapped_column(String(32))
    currency: Mapped[str] = mapped_column(String(3))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    due_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(32), default="requested", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    purpose: Mapped[str] = mapped_column(Text)
    policy_json: Mapped[str] = mapped_column(Text)
    settlement_json: Mapped[str] = mapped_column(Text, default="{}")
    history_json: Mapped[str] = mapped_column(Text, default="[]")
