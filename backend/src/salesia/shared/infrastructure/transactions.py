import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4
from fastapi import HTTPException
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, false, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column
from salesia.shared.infrastructure.database import Base


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), primary_key=True)
    operation: Mapped[str] = mapped_column(String(128), primary_key=True)
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    response_json: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class DocumentSequence(Base):
    __tablename__ = "document_sequences"
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), primary_key=True)
    series: Mapped[str] = mapped_column(String(16), primary_key=True)
    value: Mapped[int] = mapped_column(Integer, default=0)


class RefundModel(Base):
    __tablename__ = "payment_refunds"
    unapplied_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    cash_session_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("cash_sessions.id"), nullable=True)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    payment_id: Mapped[UUID] = mapped_column(ForeignKey("payments.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    reason: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="confirmed")
    provider_reference: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    return_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


def claim_request(db, company_id, operation, key, payload):
    if key is None:
        return None, None
    if not key.strip() or len(key) > 128:
        raise HTTPException(422, "La clave de idempotencia debe contener entre 1 y 128 caracteres.")
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
    identity = {"company_id": company_id, "operation": operation, "key": key}
    record = db.get(IdempotencyRecord, identity)
    if record:
        if record.request_hash != digest:
            raise HTTPException(409, "La clave ya se utilizó con otra solicitud.")
        if record.response_json is None:
            raise HTTPException(409, "Solicitud en curso. Reintente con la misma clave.")
        return record, json.loads(record.response_json)
    record = IdempotencyRecord(**identity, request_hash=digest)
    try:
        with db.begin_nested():
            db.add(record)
            db.flush()
    except IntegrityError:
        raise HTTPException(409, "Solicitud concurrente. Reintente con la misma clave.")
    return record, None


def complete_request(record, response):
    if record:
        record.response_json = json.dumps(response, default=str)


def next_number(db, company_id, series):
    identity = {"company_id": company_id, "series": series}
    if db.get(DocumentSequence, identity) is None:
        try:
            with db.begin_nested():
                db.add(DocumentSequence(**identity, value=0))
                db.flush()
        except IntegrityError:
            pass
    return db.scalar(update(DocumentSequence).where(DocumentSequence.company_id == company_id, DocumentSequence.series == series).values(value=DocumentSequence.value + 1).returning(DocumentSequence.value))


class CompanySettings(Base):
    __tablename__ = "company_settings"
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    values_json: Mapped[str] = mapped_column(Text, default="{}")
