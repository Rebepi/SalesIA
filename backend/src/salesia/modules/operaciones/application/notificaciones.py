import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application.auxiliares.now import now
from salesia.modules.operaciones.application.contracts.notificaciones import (
    NotificationPreferenceRequest,
    NotificationReadRequest,
)
from salesia.modules.operaciones.infrastructure_models import Notification, NotificationPreference
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainForbiddenException
from salesia.shared.infrastructure.models import UserModel


def list_notifications(
    limit: int,
    offset: int,
    priority: Optional[str],
    category: Optional[str],
    event_type: Optional[str],
    unread_only: bool,
    cursor: Optional[str],
    current_user: AuthenticatedUser,
    db: Session,
):
    q = select(Notification).where(
        Notification.company_id == current_user.company_id, Notification.user_id == current_user.user_id
    )

    if priority:
        q = q.where(Notification.priority == priority)

    if category:
        q = q.where(Notification.category == category)

    if event_type:
        q = q.where(Notification.event_type == event_type)

    if unread_only:
        q = q.where(Notification.read_at.is_(None))

    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)

            q = q.where(Notification.created_at < cursor_dt)

        except Exception:
            pass

    total_count = db.scalar(select(func.count()).select_from(q.subquery())) or 0

    rows = db.scalars(q.order_by(Notification.created_at.desc()).offset(offset).limit(limit)).all()

    unread = (
        db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.company_id == current_user.company_id,
                Notification.user_id == current_user.user_id,
                Notification.read_at.is_(None),
            )
        )
        or 0
    )

    next_cursor = rows[-1].created_at.isoformat() if len(rows) == limit else None

    return {
        "items": [
            {
                "id": str(row.id),
                "title": row.title,
                "message": row.message,
                "event_type": row.event_type,
                "priority": row.priority,
                "category": row.category,
                "resource_type": row.resource_type,
                "resource_id": str(row.resource_id) if row.resource_id else None,
                "read": row.read_at is not None,
                "read_at": row.read_at.isoformat() if row.read_at else None,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ],
        "total_count": total_count,
        "unread_count": unread,
        "cursor": next_cursor,
    }


def mark_all_notifications_read(current_user: AuthenticatedUser, db: Session):
    changed = db.execute(
        update(Notification)
        .where(
            Notification.company_id == current_user.company_id,
            Notification.user_id == current_user.user_id,
            Notification.read_at.is_(None),
        )
        .values(read_at=now())
        .execution_options(synchronize_session=False)
    )

    db.commit()

    return {"marked_read_count": changed.rowcount or 0}


def mark_notification_read(
    notification_id: UUID, payload: NotificationReadRequest, current_user: AuthenticatedUser, db: Session
):
    row = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.company_id == current_user.company_id,
            Notification.user_id == current_user.user_id,
        )
    )

    if not row:
        other = db.scalar(select(Notification).where(Notification.id == notification_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Notificación no encontrada.")

    row.read_at = now() if payload.read else None

    db.commit()

    return {"id": str(notification_id), "read": payload.read}


def get_notification_resource(notification_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.company_id == current_user.company_id,
            Notification.user_id == current_user.user_id,
        )
    )

    if not row:
        other = db.scalar(select(Notification).where(Notification.id == notification_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Notificación no encontrada.")

    user = db.scalar(
        select(UserModel).where(
            UserModel.id == current_user.user_id,
            UserModel.company_id == current_user.company_id,
            UserModel.is_active.is_(True),
        )
    )

    if not user:
        raise DomainForbiddenException("Membresía inactiva; acceso al recurso revocado.")

    perm_map = {
        "customer": "customers:read",
        "product": "products:read",
        "sale": "sales:read",
        "inventory": "inventory:read",
    }

    needed = perm_map.get(row.resource_type or "")

    if needed and needed not in current_user.permissions:
        raise DomainForbiddenException("Permiso insuficiente o acceso revocado al recurso.")

    from salesia.modules.operaciones.application.recursos import RESOURCES, entity
    if row.resource_type in RESOURCES and row.resource_id:
        entity(db, current_user, row.resource_type, row.resource_id)
    if row.resource_type == "report_run" and row.resource_id:
        from salesia.modules.analitica.application.reportes.operativos import authorize_report
        from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
        if "reports:read" not in current_user.permissions:
            raise DomainForbiddenException("El acceso a reportes fue revocado.")
        artifact = db.scalar(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == current_user.company_id, AnalyticsArtifact.id == row.resource_id, AnalyticsArtifact.kind == "report_run"))
        if artifact is None:
            raise HTTPException(404, "El reporte ya no está disponible.")
        data = json.loads(artifact.data_json)
        authorize_report(current_user, data["report_type"])
        expiry = datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
        if expiry and expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if data.get("is_revoked") or (expiry and expiry <= datetime.now(timezone.utc)):
            raise HTTPException(410, "El reporte caducó o fue revocado. Solicita una nueva ejecución.")
    if row.resource_type == "approval" and row.resource_id:
        from salesia.modules.operaciones.infrastructure_models import CollaborationApproval
        approval = db.scalar(select(CollaborationApproval).where(CollaborationApproval.company_id == current_user.company_id, CollaborationApproval.id == row.resource_id))
        if approval is None:
            raise HTTPException(404, "La aprobación ya no está disponible.")
        if approval.requested_by != current_user.user_id and "approvals:manage" not in current_user.permissions:
            raise DomainForbiddenException("No tienes acceso a esta aprobación.")
        entity(db, current_user, approval.resource_type, approval.resource_id)

    return {
        "notification_id": str(row.id),
        "resource_type": row.resource_type,
        "resource_id": str(row.resource_id) if row.resource_id else None,
        "access_granted": True,
    }


def get_notification_preferences(current_user: AuthenticatedUser, db: Session):
    rows = db.scalars(
        select(NotificationPreference).where(
            NotificationPreference.company_id == current_user.company_id,
            NotificationPreference.user_id == current_user.user_id,
        )
    ).all()

    defaults = {
        ("commercial", "in_app"): True,
        ("commercial", "email"): True,
        ("marketing", "in_app"): True,
        ("marketing", "email"): False,
        ("operations", "in_app"): True,
        ("operations", "email"): True,
        ("security", "in_app"): True,
        ("security", "email"): True,
    }

    for row in rows:
        defaults[(row.category, row.channel)] = row.enabled

    return {
        "preferences": [
            {"category": cat, "channel": ch, "enabled": defaults[(cat, ch)], "is_mandatory": cat == "security"}
            for (cat, ch) in sorted(defaults.keys())
        ]
    }


def update_notification_preference(
    payload: NotificationPreferenceRequest, current_user: AuthenticatedUser, db: Session
):
    if payload.category == "security" and not payload.enabled:
        raise HTTPException(400, "Los avisos críticos de seguridad son obligatorios y no se pueden desactivar.")

    pref = db.scalar(
        select(NotificationPreference)
        .where(
            NotificationPreference.company_id == current_user.company_id,
            NotificationPreference.user_id == current_user.user_id,
            NotificationPreference.category == payload.category,
            NotificationPreference.channel == payload.channel,
        )
        .with_for_update()
    )

    if pref:
        pref.enabled = payload.enabled

        pref.schedule_start = payload.schedule_start

        pref.schedule_end = payload.schedule_end

        pref.updated_at = now()

    else:
        pref = NotificationPreference(
            company_id=current_user.company_id,
            user_id=current_user.user_id,
            category=payload.category,
            channel=payload.channel,
            enabled=payload.enabled,
            schedule_start=payload.schedule_start,
            schedule_end=payload.schedule_end,
            updated_at=now(),
        )

        db.add(pref)

    db.commit()

    return {
        "category": pref.category,
        "channel": pref.channel,
        "enabled": pref.enabled,
        "schedule_start": pref.schedule_start,
        "schedule_end": pref.schedule_end,
    }
