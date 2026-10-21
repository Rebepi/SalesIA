from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.notificaciones as service_notificaciones
from salesia.modules.operaciones.application.contracts.notificaciones import (
    NotificationPreferenceRequest,
    NotificationReadRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/notifications")
def list_notifications(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    unread_only: bool = Query(False),
    cursor: Optional[str] = Query(None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_notificaciones.list_notifications(
        limit=limit,
        offset=offset,
        priority=priority,
        category=category,
        event_type=event_type,
        unread_only=unread_only,
        cursor=cursor,
        current_user=current_user,
        db=db,
    )


@router.patch("/notifications/read-all")
def mark_all_notifications_read(
    current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_notificaciones.mark_all_notifications_read(current_user=current_user, db=db)


@router.patch("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: UUID,
    payload: NotificationReadRequest = NotificationReadRequest(),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_notificaciones.mark_notification_read(
        notification_id=notification_id, payload=payload, current_user=current_user, db=db
    )


@router.get("/notifications/{notification_id}/resource")
def get_notification_resource(
    notification_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_notificaciones.get_notification_resource(
        notification_id=notification_id, current_user=current_user, db=db
    )


@router.get("/notifications/preferences")
def get_notification_preferences(
    current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_notificaciones.get_notification_preferences(current_user=current_user, db=db)


@router.put("/notifications/preferences")
def update_notification_preference(
    payload: NotificationPreferenceRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_notificaciones.update_notification_preference(payload=payload, current_user=current_user, db=db)
