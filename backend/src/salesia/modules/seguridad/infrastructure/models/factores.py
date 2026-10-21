from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base


class AuthFactor(Base):
    __tablename__ = "auth_factors"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    encrypted_secret: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    last_counter: Mapped[int] = mapped_column(Integer, default=-1)


class RecoveryCode(Base):
    __tablename__ = "auth_recovery_codes"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    code_hash: Mapped[str] = mapped_column(String(64), unique=True)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
