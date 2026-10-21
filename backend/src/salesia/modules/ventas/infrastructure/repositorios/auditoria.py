from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from salesia.modules.ventas.domain.ports import IAuditPort
from salesia.shared.infrastructure.models import AuditLogModel


class SqlAuditPort(IAuditPort):
    def __init__(self, session: Session):
        self.session = session

    def record_action(
        self,
        company_id: UUID,
        actor_id: Optional[UUID],
        actor_email: str,
        action: str,
        entity_type: str,
        entity_id: UUID,
        payload_diff: str,
    ) -> None:
        self.session.add(
            AuditLogModel(
                id=uuid4(),
                company_id=company_id,
                actor_id=actor_id,
                actor_email=actor_email,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                trace_id=uuid4().hex,
                payload_diff=payload_diff,
                created_at=datetime.now(timezone.utc),
            )
        )
        self.session.flush()
