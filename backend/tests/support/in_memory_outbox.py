from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Any, Optional
from uuid import UUID, uuid4
import random


@dataclass
class OutboxRecord:
    event_id: UUID
    event_type: str
    company_id: UUID
    payload: dict[str, Any]
    status: str = "pending"
    retry_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: Optional[datetime] = None


class InMemoryOutboxRepository:
    def __init__(self):
        self._records: dict[UUID, OutboxRecord] = {}

    def save(self, record: OutboxRecord) -> None:
        self._records[record.event_id] = record

    def get_pending(self, limit: int = 100) -> list[OutboxRecord]:
        pending = [r for r in self._records.values() if r.status == "pending"]
        return sorted(pending, key=lambda x: x.created_at)[:limit]

    def mark_published(self, event_id: UUID) -> None:
        if event_id in self._records:
            self._records[event_id].status = "published"
            self._records[event_id].published_at = datetime.now(timezone.utc)

    def mark_failed(self, event_id: UUID) -> None:
        if event_id in self._records:
            self._records[event_id].retry_count += 1
            if self._records[event_id].retry_count >= 5:
                self._records[event_id].status = "dead_letter"

    def get_by_id(self, event_id: UUID) -> Optional[OutboxRecord]:
        return self._records.get(event_id)


class InboxDeduplicator:
    def __init__(self):
        self._processed_events: set[UUID] = set()

    def is_processed(self, event_id: UUID) -> bool:
        return event_id in self._processed_events

    def mark_processed(self, event_id: UUID) -> None:
        self._processed_events.add(event_id)


class OutboxDispatcher:
    def __init__(
        self,
        repository: InMemoryOutboxRepository,
        deduplicator: InboxDeduplicator,
        publisher_func: Optional[Callable[[OutboxRecord], bool]] = None
    ):
        self.repository = repository
        self.deduplicator = deduplicator
        self.publisher_func = publisher_func or (lambda rec: True)

    def calculate_backoff(self, retry_count: int) -> float:
        base_delay = 0.1 * (2 ** retry_count)
        jitter = random.uniform(0.01, 0.05)
        return min(base_delay + jitter, 10.0)

    def dispatch_batch(self, limit: int = 50) -> int:
        records = self.repository.get_pending(limit=limit)
        success_count = 0

        for record in records:
            if self.deduplicator.is_processed(record.event_id):
                self.repository.mark_published(record.event_id)
                success_count += 1
                continue

            try:
                delivered = self.publisher_func(record)
                if delivered:
                    self.deduplicator.mark_processed(record.event_id)
                    self.repository.mark_published(record.event_id)
                    success_count += 1
                else:
                    self.repository.mark_failed(record.event_id)
            except Exception:
                self.repository.mark_failed(record.event_id)

        return success_count
