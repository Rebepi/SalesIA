import json

from sqlalchemy.orm import Session

from salesia.modules.ventas.domain.ports import IOutboxPort
from salesia.shared.infrastructure.models import OutboxEventModel
from salesia.shared.infrastructure.outbox import OutboxRecord


class SqlOutboxAdapter(IOutboxPort):
    def __init__(self, session: Session):
        self.session = session

    def record_event(self, event: OutboxRecord) -> None:
        self.session.add(
            OutboxEventModel(
                id=event.event_id,
                company_id=event.company_id,
                event_type=event.event_type,
                aggregate_type="Sale",
                aggregate_id=event.payload.get("sale_id", event.event_id),
                payload_json=json.dumps(event.payload, sort_keys=True, separators=(",", ":")),
                status="PENDING",
                retry_count=event.retry_count,
                created_at=event.created_at,
            )
        )
        self.session.flush()
