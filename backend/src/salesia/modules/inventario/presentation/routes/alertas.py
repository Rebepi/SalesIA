from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.alertas as service_alertas
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/inventory/alerts")
def list_alerts(
    current_user: AuthenticatedUser = Depends(require_permission("inventory:read")), db: Session = Depends(get_db)
):

    return service_alertas.list_alerts(current_user=current_user, db=db)


@router.post("/inventory/alerts/recalculate")
def trigger_alert_recalculation(
    current_user: AuthenticatedUser = Depends(require_permission("inventory:read")), db: Session = Depends(get_db)
):

    return service_alertas.trigger_alert_recalculation(current_user=current_user, db=db)


@router.post("/inventory/alerts/{alert_id}/resolve")
def resolve_alert_endpoint(
    alert_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_alertas.resolve_alert_endpoint(alert_id=alert_id, current_user=current_user, db=db)
