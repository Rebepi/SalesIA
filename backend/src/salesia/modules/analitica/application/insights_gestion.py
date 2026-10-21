import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.analitica.application.contracts.insights_gestion import (
    InsightBulkActionRequest,
    InsightFeedbackRequest,
    InsightStatusUpdateRequest,
)
from salesia.modules.analitica.domain.insights import redact_insight_for_user
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact, CollaborationTask
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import CustomerModel, ProductModel, SaleModel, UserModel


def list_insights(
    status_filter: Optional[str],
    severity_filter: Optional[str],
    rule_id: Optional[str],
    entity_type: Optional[str],
    limit: int,
    offset: int,
    current_user: AuthenticatedUser,
    db: Session,
):
    query = select(AnalyticsArtifact).where(
        AnalyticsArtifact.company_id == current_user.company_id, AnalyticsArtifact.kind == "insight"
    )

    if status_filter:
        query = query.where(AnalyticsArtifact.status == status_filter)

    rows = db.scalars(query.order_by(AnalyticsArtifact.created_at.desc())).all()

    can_view_costs = "products:cost:read" in current_user.permissions or current_user.role in (
        "company_admin",
        "manager",
        "purchaser",
    )

    results = []

    for row in rows:
        data = json.loads(row.data_json)

        if severity_filter and data.get("severity") != severity_filter:
            continue

        if rule_id and data.get("rule_id") != rule_id:
            continue

        if entity_type and data.get("entity_type") != entity_type:
            continue

        redacted = redact_insight_for_user(data, can_view_costs)

        results.append(redacted)

    paginated = results[offset : offset + limit]

    return {"items": paginated, "count": len(paginated), "total": len(results)}


def get_insight_detail(insight_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.id == insight_id,
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "insight",
        )
    )

    if not row:
        raise HTTPException(404, "Insight no encontrado.")

    data = json.loads(row.data_json)

    can_view_costs = "products:cost:read" in current_user.permissions or current_user.role in (
        "company_admin",
        "manager",
        "purchaser",
    )

    return redact_insight_for_user(data, can_view_costs)


def get_insight_evidence(insight_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.id == insight_id,
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "insight",
        )
    )

    if not row:
        raise HTTPException(404, "Insight no encontrado.")

    data = json.loads(row.data_json)

    can_view_costs = "products:cost:read" in current_user.permissions or current_user.role in (
        "company_admin",
        "manager",
        "purchaser",
    )

    redacted = redact_insight_for_user(data, can_view_costs)

    return {
        "insight_id": str(row.id),
        "rule_id": redacted.get("rule_id"),
        "rule_definition": redacted.get("rule_definition"),
        "evidence_data": redacted.get("evidence_data"),
        "evidence_summary": redacted.get("evidence"),
        "observation": redacted.get("observation"),
        "interpretation": redacted.get("interpretation"),
        "suggested_action": redacted.get("suggested_action"),
    }


def update_insight_status(
    insight_id: UUID, payload: InsightStatusUpdateRequest, current_user: AuthenticatedUser, db: Session
):
    row = db.scalar(
        select(AnalyticsArtifact)
        .where(
            AnalyticsArtifact.id == insight_id,
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "insight",
        )
        .with_for_update()
    )

    if not row:
        raise HTTPException(404, "Insight no encontrado.")

    data = json.loads(row.data_json)

    if payload.version is not None and data.get("version") != payload.version:
        raise HTTPException(status_code=409, detail="Conflicto de concurrencia: versión no coincide.")

    data["status"] = payload.status

    data["updated_at"] = datetime.now(timezone.utc).isoformat()

    data.setdefault("lifecycle_history", []).append(
        {
            "previous_status": row.status,
            "new_status": payload.status,
            "reason": payload.reason or "Actualización de estado",
            "changed_by": str(current_user.user_id),
            "changed_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    row.status = payload.status

    row.data_json = json.dumps(data)

    row.updated_at = datetime.now(timezone.utc)

    db.commit()

    can_view_costs = "products:cost:read" in current_user.permissions or current_user.role in (
        "company_admin",
        "manager",
        "purchaser",
    )

    return redact_insight_for_user(data, can_view_costs)


def add_insight_feedback(
    insight_id: UUID, payload: InsightFeedbackRequest, current_user: AuthenticatedUser, db: Session
):
    row = db.scalar(
        select(AnalyticsArtifact)
        .where(
            AnalyticsArtifact.id == insight_id,
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "insight",
        )
        .with_for_update()
    )

    if not row:
        raise HTTPException(404, "Insight no encontrado.")

    data = json.loads(row.data_json)

    feedback_entry = {
        "feedback_id": str(uuid4()),
        "user_id": str(current_user.user_id),
        "user_email": current_user.email,
        "company_id": str(current_user.company_id),
        "helpful": payload.helpful,
        "comment": payload.comment or payload.reason or "",
        "reason": payload.reason or payload.comment or "",
        "rule_id": data.get("rule_id", ""),
        "segment": data.get("entity_type", "Product"),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }

    data.setdefault("feedback", []).append(feedback_entry)

    row.data_json = json.dumps(data)

    row.updated_at = datetime.now(timezone.utc)

    db.commit()

    return {"insight_id": str(insight_id), "helpful": payload.helpful, "recorded": True}


def prepare_insight_action(insight_id: UUID, action_id: str, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.id == insight_id,
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "insight",
        )
    )

    if not row:
        raise HTTPException(404, "Insight no encontrado.")

    data = json.loads(row.data_json)

    actions = data.get("suggested_actions", [])

    target_action = next((a for a in actions if a.get("action_id") == action_id), None)

    if not target_action:
        raise HTTPException(404, "Acción sugerida no encontrada.")

    return {
        "insight_id": str(row.id),
        "action_id": action_id,
        "action_type": target_action.get("action_type"),
        "title": target_action.get("title"),
        "description": target_action.get("description"),
        "draft_preview": target_action.get("draft_preview"),
        "projected_impact": target_action.get("projected_impact"),
        "can_auto_execute_finance": False,
        "requires_manual_confirmation": True,
        "prepared_at": datetime.now(timezone.utc).isoformat(),
    }


def bulk_insight_actions(payload: InsightBulkActionRequest, current_user: AuthenticatedUser, db: Session):
    ids = set(payload.ids)

    rows = db.scalars(
        select(AnalyticsArtifact)
        .where(
            AnalyticsArtifact.id.in_(ids),
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "insight",
        )
        .order_by(AnalyticsArtifact.id)
        .with_for_update()
    ).all()

    if len(rows) != len(ids):
        raise HTTPException(404, "Una de las alertas no está disponible en esta empresa.")

    if payload.action == "snooze" and (
        not payload.snoozed_until
        or payload.snoozed_until.tzinfo is None
        or payload.snoozed_until <= datetime.now(timezone.utc)
    ):
        raise HTTPException(422, "Selecciona una fecha futura para volver a mostrar las alertas.")

    if payload.action == "task":
        if (
            not payload.assignee_id
            or not payload.due_date
            or payload.due_date.tzinfo is None
            or payload.due_date <= datetime.now(timezone.utc)
        ):
            raise HTTPException(422, "Selecciona un responsable y una fecha futura para la tarea.")

        member = db.scalar(
            select(UserModel).where(
                UserModel.id == payload.assignee_id,
                UserModel.company_id == current_user.company_id,
                UserModel.is_active.is_(True),
            )
        )

        if not member:
            raise HTTPException(422, "El responsable no es una membresía activa de esta empresa.")

    task_ids = []

    for row in rows:
        data = json.loads(row.data_json)

        previous = data.get("status", row.status)

        if payload.action == "snooze":
            data["snoozed_until"] = payload.snoozed_until.isoformat()

        elif payload.action == "task":
            existing_id = data.get("task_id")

            existing = (
                db.scalar(
                    select(CollaborationTask).where(
                        CollaborationTask.id == UUID(existing_id),
                        CollaborationTask.company_id == current_user.company_id,
                        CollaborationTask.status.in_(["pending", "in_progress"]),
                    )
                )
                if existing_id
                else None
            )

            if existing:
                task_ids.append(str(existing.id))

                continue

            resource_type = str(data.get("entity_type", "")).lower()

            resource_id = data.get("entity_id")

            models = {"customer": CustomerModel, "product": ProductModel, "sale": SaleModel}

            model = models.get(resource_type)

            try:
                resolved_id = UUID(str(resource_id)) if resource_id else None

            except ValueError:
                resolved_id = None

            if (
                not model
                or not resolved_id
                or not db.scalar(
                    select(model.id).where(model.id == resolved_id, model.company_id == current_user.company_id)
                )
            ):
                resource_type, resolved_id = None, None

            can_view_costs = "products:cost:read" in current_user.permissions or current_user.role in (
                "company_admin",
                "manager",
                "purchaser",
            )

            task_data = redact_insight_for_user(data, can_view_costs)

            task = CollaborationTask(
                company_id=current_user.company_id,
                title=str(task_data.get("title") or "Revisar alerta comercial")[:255],
                description=f"{task_data.get('suggested_action') or task_data.get('interpretation') or ''}\n{payload.notes}".strip(),
                creator_id=current_user.user_id,
                assignee_id=payload.assignee_id,
                due_date=payload.due_date,
                priority=payload.priority,
                resource_type=resource_type,
                resource_id=resolved_id,
                status="pending",
            )

            db.add(task)

            db.flush()

            data["task_id"] = str(task.id)

            data["assignee_id"] = str(payload.assignee_id)

            data["status"] = "in_review"

            task_ids.append(str(task.id))

        else:
            data["status"] = {"read": "read", "dismiss": "dismissed", "resolve": "resolved"}[payload.action]

            data.pop("snoozed_until", None)

        data.setdefault("lifecycle_history", []).append(
            {
                "previous_status": previous,
                "new_status": data.get("status", previous),
                "action": payload.action,
                "reason": payload.notes,
                "changed_by": str(current_user.user_id),
                "changed_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        row.status = data.get("status", row.status)

        row.data_json = json.dumps(data)

    db.commit()

    return {"updated_count": len(rows), "task_ids": task_ids}


def bulk_read_insights(current_user: AuthenticatedUser, db: Session):
    rows = db.scalars(
        select(AnalyticsArtifact)
        .where(
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "insight",
            AnalyticsArtifact.status.in_(["new", "pending"]),
        )
        .with_for_update()
    ).all()

    now = datetime.now(timezone.utc)

    for row in rows:
        data = json.loads(row.data_json)

        data["status"] = "read"

        data.setdefault("lifecycle_history", []).append(
            {
                "previous_status": row.status,
                "new_status": "read",
                "reason": "Lectura masiva",
                "changed_by": str(current_user.user_id),
                "changed_at": now.isoformat(),
            }
        )

        row.status = "read"

        row.data_json = json.dumps(data)

        row.updated_at = now

    db.commit()

    return {"status": "success", "marked_read_count": len(rows)}
