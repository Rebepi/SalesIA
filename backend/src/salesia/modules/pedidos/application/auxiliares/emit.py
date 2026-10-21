import json

from salesia.shared.infrastructure.models import OutboxEventModel


def emit(db, company_id, event_type, aggregate_type, aggregate_id, payload):

    db.add(
        OutboxEventModel(
            company_id=company_id,
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload_json=json.dumps(payload, default=str),
            status="PENDING",
        )
    )
