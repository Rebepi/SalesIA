from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class CashSessionModel(Base, TimestampMixin):
    __tablename__ = "cash_sessions"
    __table_args__ = (
        Index(
            "uq_cash_sessions_open_terminal",
            "company_id",
            "terminal_code",
            unique=True,
            postgresql_where=text("status = 'open'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    branch_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    terminal_code: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    initial_cash: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    expected_cash: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0.000000"), nullable=False)
    actual_cash: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 6), nullable=True)
    difference_cash: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 6), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    movements_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    count_control_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
