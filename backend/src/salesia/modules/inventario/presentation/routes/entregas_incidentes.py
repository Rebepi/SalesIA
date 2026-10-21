from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.entregas_incidentes as service_entregas_incidentes
from salesia.modules.inventario.application.contracts.entregas_incidentes import (
    DeliveryIncidentCreateRequest,
    ProofOfDeliveryRequest,
    TrackingEventCreateRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/deliveries/{delivery_id}/tracking-events", status_code=201)
def record_tracking_event(
    delivery_id: UUID,
    payload: TrackingEventCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_entregas_incidentes.record_tracking_event(
        delivery_id=delivery_id, payload=payload, current_user=current_user, db=db
    )


@router.post("/deliveries/{delivery_id}/proof-of-delivery", status_code=201)
def record_proof_of_delivery(
    delivery_id: UUID,
    payload: ProofOfDeliveryRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_entregas_incidentes.record_proof_of_delivery(
        delivery_id=delivery_id, payload=payload, current_user=current_user, db=db
    )


@router.get("/deliveries/{delivery_id}/proof-of-delivery")
def get_proof_of_delivery(
    delivery_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_entregas_incidentes.get_proof_of_delivery(delivery_id=delivery_id, current_user=current_user, db=db)


@router.post("/deliveries/{delivery_id}/incidents", status_code=201)
def record_delivery_incident(
    delivery_id: UUID,
    payload: DeliveryIncidentCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_entregas_incidentes.record_delivery_incident(
        delivery_id=delivery_id, payload=payload, current_user=current_user, db=db
    )
