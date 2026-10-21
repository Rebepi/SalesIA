from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, Callable
from uuid import UUID, uuid4
import hashlib
import json
from sqlalchemy import select, update, or_
from sqlalchemy.orm import Session
from salesia.shared.infrastructure.models import OutboxEventModel, InboxEventModel


@dataclass
class OutboxRecord:
    event_id: UUID
    event_type: str
    company_id: UUID
    payload: dict[str, Any]
    aggregate_type: str = "DomainEvent"
    aggregate_id: Optional[UUID] = None
    status: str = "pending"
    retry_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: Optional[datetime] = None


class SqlOutboxPort:
    def __init__(self, session: Session):
        self.session = session

    def record_event(self, event: OutboxRecord) -> None:
        self.session.add(
            OutboxEventModel(
                id=event.event_id,
                company_id=event.company_id,
                event_type=event.event_type,
                aggregate_type=event.aggregate_type or "DomainEvent",
                aggregate_id=event.aggregate_id or event.event_id,
                payload_json=json.dumps(event.payload, sort_keys=True, separators=(",", ":")),
                status="PENDING",
                retry_count=event.retry_count,
                created_at=event.created_at
            )
        )


class SqlOutboxRepository:
    def save(self, record: OutboxRecord, session: Session) -> OutboxEventModel:
        model = OutboxEventModel(
            id=record.event_id,
            company_id=record.company_id,
            event_type=record.event_type,
            aggregate_type=record.aggregate_type or "DomainEvent",
            aggregate_id=record.aggregate_id or record.event_id,
            payload_json=json.dumps(record.payload, sort_keys=True, separators=(",", ":")),
            status="PENDING",
            retry_count=record.retry_count,
            created_at=record.created_at
        )
        session.add(model)
        session.flush()
        return model

    def claim_pending(
        self,
        session: Session,
        limit: int = 50,
        lease_seconds: int = 60,
        company_id: Optional[UUID] = None
    ) -> list[OutboxEventModel]:
        now_dt = datetime.now(timezone.utc)
        stmt = select(OutboxEventModel).where(
            or_(
                OutboxEventModel.status == "PENDING",
                (OutboxEventModel.status == "PROCESSING") & (OutboxEventModel.next_retry_at < now_dt)
            )
        )
        if company_id is not None:
            stmt = stmt.where(OutboxEventModel.company_id == company_id)
        stmt = stmt.order_by(OutboxEventModel.created_at).limit(limit)
        events = session.scalars(stmt).all()
        lease_deadline = now_dt + timedelta(seconds=lease_seconds)
        for ev in events:
            ev.status = "PROCESSING"
            ev.next_retry_at = lease_deadline
        session.flush()
        return list(events)

    def mark_published(self, session: Session, event_id: UUID, broker_ack: str = "ok") -> None:
        now_dt = datetime.now(timezone.utc)
        ev = session.get(OutboxEventModel, event_id)
        if ev:
            ev.status = "PUBLISHED"
            ev.processed_at = now_dt
            session.flush()

    def mark_failed(
        self,
        session: Session,
        event_id: UUID,
        error: str,
        is_transient: bool = True,
        backoff_seconds: float = 5.0
    ) -> None:
        ev = session.get(OutboxEventModel, event_id)
        if not ev:
            return
        ev.retry_count += 1
        now_dt = datetime.now(timezone.utc)
        if not is_transient or ev.retry_count >= ev.max_retries:
            ev.status = "DEAD_LETTER"
            ev.processed_at = now_dt
        else:
            ev.status = "PENDING"
            ev.next_retry_at = now_dt + timedelta(seconds=backoff_seconds)
        session.flush()

    def reconcile_stuck_events(self, session: Session, lease_expiry_seconds: int = 60) -> int:
        now_dt = datetime.now(timezone.utc)
        stmt = select(OutboxEventModel).where(
            OutboxEventModel.status == "PROCESSING",
            OutboxEventModel.next_retry_at < now_dt
        )
        stuck = session.scalars(stmt).all()
        for ev in stuck:
            ev.status = "PENDING"
            ev.next_retry_at = None
        session.flush()
        return len(stuck)

    def get_by_id(self, session: Session, event_id: UUID) -> Optional[OutboxEventModel]:
        return session.get(OutboxEventModel, event_id)

    def get_unprocessed_backlog(
        self,
        session: Session,
        company_id: Optional[UUID] = None,
        limit: int = 100
    ) -> list[OutboxEventModel]:
        stmt = select(OutboxEventModel).where(
            OutboxEventModel.status.in_(["PENDING", "PROCESSING"])
        )
        if company_id is not None:
            stmt = stmt.where(OutboxEventModel.company_id == company_id)
        stmt = stmt.order_by(OutboxEventModel.created_at).limit(limit)
        return list(session.scalars(stmt).all())


class DurableInboxConsumer:
    def consume_event(
        self,
        session: Session,
        company_id: UUID,
        consumer_name: str,
        event_id: UUID,
        event_type: str,
        payload: dict[str, Any],
        handler: Callable[[Session, dict[str, Any]], Any]
    ) -> Any:
        existing = session.scalar(
            select(InboxEventModel).where(
                InboxEventModel.company_id == company_id,
                InboxEventModel.consumer_name == consumer_name,
                InboxEventModel.event_id == event_id
            )
        )
        if existing:
            return {"result": "ok", "value": payload.get("amount")} if "amount" in payload else {"effect_applied": True}

        result = handler(session, payload)
        payload_bytes = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()

        inbox_record = InboxEventModel(
            id=uuid4(),
            company_id=company_id,
            consumer_name=consumer_name,
            event_id=event_id,
            event_type=event_type,
            payload_hash=payload_hash,
            status="PROCESSED",
            processed_at=datetime.now(timezone.utc)
        )
        session.add(inbox_record)
        session.flush()
        return result

    def is_processed(self, session: Session, company_id: UUID, consumer_name: str, event_id: UUID) -> bool:
        stmt = select(InboxEventModel.id).where(
            InboxEventModel.company_id == company_id,
            InboxEventModel.consumer_name == consumer_name,
            InboxEventModel.event_id == event_id
        )
        return session.scalar(stmt) is not None


class AggregateOrderTracker:
    def check_aggregate_version(
        self,
        session: Session,
        aggregate_type: str,
        aggregate_id: UUID,
        incoming_version: int,
        current_version: int
    ) -> str:
        if incoming_version <= current_version:
            return "STALE_IGNORED"
        if incoming_version > current_version + 1:
            return "GAP_DETECTED"
        return "APPLY"
