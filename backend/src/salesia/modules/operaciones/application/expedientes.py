import json
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select

from salesia.modules.operaciones.application.recursos import RELATIONS, RESOURCES, definition, entity, entity_statement, search_statement, summary
from salesia.shared.infrastructure.models import AuditLogModel


def resource_catalog(user):
    return [{"type": kind, "label": resource[1], "can_write": not resource[3] or resource[3] in user.permissions} for kind, resource in RESOURCES.items() if not resource[2] or resource[2] in user.permissions]


def list_records(db, user, kind, query, limit, offset, field_key=None, field_value=None):
    statement = search_statement(kind, user, query)
    if field_key:
        from salesia.modules.operaciones.infrastructure.models.campos import BusinessFieldValuesModel
        values = db.scalars(select(BusinessFieldValuesModel).where(BusinessFieldValuesModel.company_id == user.company_id, BusinessFieldValuesModel.resource_type == kind)).all()
        ids = [row.resource_id for row in values if str(json.loads(row.values_json).get(field_key, "")).casefold() == (field_value or "").casefold()]
        statement = statement.where(RESOURCES[kind][0].id.in_(ids))
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    model = definition(kind, user)[0]
    rows = db.scalars(statement.order_by(model.id).offset(offset).limit(limit)).all()
    return {"items": [summary(kind, row) for row in rows], "total_count": total}


def dossier(db, user, kind, identifier):
    row = entity(db, user, kind, identifier)
    related = {}
    direct = []
    for field, target_kind in RELATIONS.items():
        target_id = getattr(row, field, None)
        if target_id and target_kind in RESOURCES:
            direct.append((target_kind, target_id))
    for target_kind, target_id in direct:
        try:
            target = entity(db, user, target_kind, target_id)
            related[(target_kind, target_id)] = summary(target_kind, target)
        except HTTPException as failure:
            if failure.status_code not in (403, 404):
                raise
    for candidate_kind, resource in RESOURCES.items():
        model = resource[0]
        if resource[2] and resource[2] not in user.permissions:
            continue
        for field, target_kind in RELATIONS.items():
            if target_kind != kind or not hasattr(model, field):
                continue
            statement = entity_statement(candidate_kind, user).where(getattr(model, field) == identifier).limit(100)
            for candidate in db.scalars(statement).all():
                if candidate.id != identifier or candidate_kind != kind:
                    related[(candidate_kind, candidate.id)] = summary(candidate_kind, candidate)
    events = []
    if "audit:logs:read" in user.permissions:
        permitted_ids = {identifier} | {UUID(item["id"]) for item in related.values()}
        logs = db.scalars(select(AuditLogModel).where(AuditLogModel.company_id == user.company_id, AuditLogModel.entity_id.in_(permitted_ids)).order_by(AuditLogModel.created_at.desc(), AuditLogModel.id).limit(200)).all()
        for log in logs:
            try:
                changes = json.loads(log.payload_diff or "{}")
            except ValueError:
                changes = {"detail": "Registro histórico sin estructura de cambios."}
            events.append({"id": str(log.id), "action": log.action, "actor": log.actor_email, "entity_id": str(log.entity_id), "date": log.created_at.isoformat(), "changes": changes})
    items = sorted(related.values(), key=lambda value: (value["created_at"] or "", value["type"], value["id"]))
    return {"resource": summary(kind, row), "related": items, "events": events, "audit_available": "audit:logs:read" in user.permissions, "limits": {"related_per_relation": 100, "events": 200}}
