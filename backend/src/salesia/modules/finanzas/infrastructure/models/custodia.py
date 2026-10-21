from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class CashCustodyAccountModel(Base, TimestampMixin):
    __tablename__ = "cash_custody_accounts"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_cash_custody_account_code"), CheckConstraint("balance >= 0", name="ck_cash_custody_account_balance"))
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    branch_id: Mapped[UUID] = mapped_column(ForeignKey("branches.id"), index=True)
    responsible_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(32))
    currency: Mapped[str] = mapped_column(String(3))
    balance: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    movements_json: Mapped[str] = mapped_column(Text, default="[]")


class CashCustodyTransferModel(Base, TimestampMixin):
    __tablename__ = "cash_custody_transfers"
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_cash_custody_transfer_code"),
        CheckConstraint("amount > 0", name="ck_cash_custody_transfer_amount"),
        CheckConstraint("(source_session_id IS NOT NULL AND source_account_id IS NULL) OR (source_session_id IS NULL AND source_account_id IS NOT NULL)", name="ck_cash_custody_source"),
        CheckConstraint("(destination_session_id IS NOT NULL AND destination_account_id IS NULL) OR (destination_session_id IS NULL AND destination_account_id IS NOT NULL)", name="ck_cash_custody_destination"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    code: Mapped[str] = mapped_column(String(32))
    currency: Mapped[str] = mapped_column(String(3))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    source_session_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("cash_sessions.id"), nullable=True, index=True)
    source_account_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("cash_custody_accounts.id"), nullable=True, index=True)
    destination_session_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("cash_sessions.id"), nullable=True, index=True)
    destination_account_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("cash_custody_accounts.id"), nullable=True, index=True)
    sender_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    receiver_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="sent", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    reason: Mapped[str] = mapped_column(Text)
    reference: Mapped[str] = mapped_column(String(128))
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    returned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    history_json: Mapped[str] = mapped_column(Text, default="[]")
