import json
from uuid import uuid4

from salesia.shared.infrastructure.models import AuditLogModel


def audit(db, user, action, entity_type, entity_id, payload):

    db.add(
        AuditLogModel(
            company_id=user.company_id,
            actor_id=user.user_id,
            actor_email=user.email,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            trace_id=uuid4().hex,
            payload_diff=json.dumps(payload, default=str),
        )
    )
