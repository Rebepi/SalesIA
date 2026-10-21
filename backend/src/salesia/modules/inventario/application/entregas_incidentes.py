import hashlib
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.inventario.application.contracts.entregas_incidentes import (
    DeliveryIncidentCreateRequest,
    ProofOfDeliveryRequest,
    TrackingEventCreateRequest,
)
from salesia.modules.inventario.infrastructure_models import (
    DeliveryIncident,
    DeliveryShipment,
    DeliveryTrackingEvent,
    ProofOfDelivery,
    SupplyDocument,
)
from salesia.modules.inventario.service import document
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def record_tracking_event(
    delivery_id: UUID, payload: TrackingEventCreateRequest, current_user: AuthenticatedUser, db: Session
):
    row = document(db, current_user, "DELIVERY", delivery_id)

    from salesia.modules.inventario.application.entregas_parciales import RESULT_STATES
    if row.status not in RESULT_STATES:
        raise HTTPException(409, "El seguimiento requiere una entrega físicamente despachada y pendiente de resolver.")
    if payload.event_status in ("ready", "dispatched", "delivered"):
        raise HTTPException(409, "Registra el despacho desde su acción y la recepción desde Resultado de entrega o Conformidad total.")
    event_time = payload.occurred_at or datetime.now(timezone.utc)

    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=timezone.utc)

    raw_hash = f"{row.company_id}:{delivery_id}:{payload.event_code}:{event_time.isoformat()}"

    dedup = hashlib.sha256(raw_hash.encode()).hexdigest()

    existing = db.scalar(
        select(DeliveryTrackingEvent).where(
            DeliveryTrackingEvent.dedup_hash == dedup, DeliveryTrackingEvent.company_id == current_user.company_id
        )
    )

    if existing:
        return {"id": str(existing.id), "deduplicated": True, "status": row.status}

    ev = DeliveryTrackingEvent(
        id=uuid4(),
        company_id=current_user.company_id,
        delivery_id=delivery_id,
        event_code=payload.event_code,
        event_status=payload.event_status,
        description=payload.description,
        location=payload.location,
        occurred_at=event_time,
        dedup_hash=dedup,
    )

    db.add(ev)

    DELIVERY_STATE_RANK = {
        "draft": 0,
        "ready": 1,
        "dispatched": 2,
        "in_transit": 3,
        "out_for_delivery": 4,
        "incident": 4,
        "failed_attempt": 4,
        "intercept_requested": 4,
        "delivered": 5,
        "cancelled": 6,
    }

    current_rank = DELIVERY_STATE_RANK.get(row.status, 0)

    new_rank = DELIVERY_STATE_RANK.get(payload.event_status, 0)

    if row.status not in ("delivered", "partially_delivered", "pending_redelivery") and new_rank >= current_rank:
        row.status = payload.event_status

        row.version += 1

        shipment = db.scalar(select(DeliveryShipment).where(DeliveryShipment.delivery_document_id == delivery_id))

        if shipment:
            shipment.status = payload.event_status

            if payload.event_status == "delivered":
                shipment.delivered_at = event_time

    db.commit()

    return {"id": str(ev.id), "deduplicated": False, "status": row.status}


def record_proof_of_delivery(
    delivery_id: UUID, payload: ProofOfDeliveryRequest, current_user: AuthenticatedUser, db: Session
):
    row = document(db, current_user, "DELIVERY", delivery_id)

    from salesia.modules.inventario.application.entregas_parciales import RESULT_STATES, full_acceptance
    if row.status == "delivered":
        existing = db.scalar(select(ProofOfDelivery).where(ProofOfDelivery.company_id == current_user.company_id, ProofOfDelivery.delivery_id == row.id))
        if existing:
            return {"id": str(existing.id), "delivery_id": str(delivery_id), "status": row.status}
    if row.status not in RESULT_STATES:
        raise HTTPException(409, "La conformidad requiere una entrega físicamente despachada y pendiente de recepción.")
    window_reservation = full_acceptance(db, current_user, row, payload.received_by_name, payload.notes or "Conformidad total del destinatario.", payload.received_by_id_doc, payload.outside_window_reason)
    deliv_time = payload.delivered_at or datetime.now(timezone.utc)

    if deliv_time.tzinfo is None:
        deliv_time = deliv_time.replace(tzinfo=timezone.utc)

    pod = db.scalar(
        select(ProofOfDelivery).where(
            ProofOfDelivery.delivery_id == delivery_id, ProofOfDelivery.company_id == current_user.company_id
        )
    )

    if not pod:
        pod = ProofOfDelivery(
            id=uuid4(),
            company_id=current_user.company_id,
            delivery_id=delivery_id,
            received_by_name=payload.received_by_name,
            received_by_id_doc=payload.received_by_id_doc,
            delivered_at=deliv_time,
            signature_data=payload.signature_data,
            photo_url=payload.photo_url,
            notes=payload.notes,
            created_by=current_user.user_id,
        )

        db.add(pod)

    row.status = "delivered"
    from salesia.modules.inventario.application.ventanas_entrega import complete_reservation
    complete_reservation(db, current_user, window_reservation, row)

    row.version += 1

    shipment = db.scalar(
        select(DeliveryShipment).where(
            DeliveryShipment.delivery_document_id == delivery_id, DeliveryShipment.company_id == current_user.company_id
        )
    )

    if shipment:
        shipment.status = "delivered"

        shipment.delivered_at = deliv_time

    db.commit()

    return {"id": str(pod.id), "delivery_id": str(delivery_id), "status": "delivered"}


def get_proof_of_delivery(delivery_id: UUID, current_user: AuthenticatedUser, db: Session):
    deliv = db.scalar(
        select(SupplyDocument).where(
            SupplyDocument.id == delivery_id,
            SupplyDocument.company_id == current_user.company_id,
            SupplyDocument.kind == "DELIVERY",
        )
    )

    if not deliv:
        raise HTTPException(404, "Entrega no encontrada.")

    if not (
        "sales:read" in current_user.permissions
        or "inventory:read" in current_user.permissions
        or current_user.role in ("company_admin", "platform_admin")
    ):
        raise HTTPException(403, "Permisos insuficientes para ver la prueba de entrega.")

    pod = db.scalar(
        select(ProofOfDelivery).where(
            ProofOfDelivery.delivery_id == delivery_id, ProofOfDelivery.company_id == current_user.company_id
        )
    )

    if not pod:
        raise HTTPException(404, "Prueba de entrega no registrada.")

    return {
        "delivery_id": str(pod.delivery_id),
        "received_by_name": pod.received_by_name,
        "received_by_id_doc": pod.received_by_id_doc,
        "delivered_at": pod.delivered_at.isoformat(),
        "signature_data": pod.signature_data,
        "photo_url": pod.photo_url,
        "notes": pod.notes,
    }


def record_delivery_incident(
    delivery_id: UUID, payload: DeliveryIncidentCreateRequest, current_user: AuthenticatedUser, db: Session
):
    row = document(db, current_user, "DELIVERY", delivery_id)

    shipment = db.scalar(
        select(DeliveryShipment).where(
            DeliveryShipment.delivery_document_id == delivery_id, DeliveryShipment.company_id == current_user.company_id
        )
    )

    from salesia.modules.inventario.application.entregas_parciales import RESULT_STATES
    if row.status not in RESULT_STATES:
        raise HTTPException(409, "Registra incidencias de reparto sobre una entrega despachada y pendiente de resolver.")
    incident = DeliveryIncident(
        id=uuid4(),
        company_id=current_user.company_id,
        delivery_id=delivery_id,
        incident_type=payload.incident_type,
        description=payload.description,
        responsible_user_id=current_user.user_id,
        rescheduled_date=payload.rescheduled_date,
        resolution_status="OPEN",
    )

    db.add(incident)

    partial_status = row.status if row.status in ("partially_delivered", "pending_redelivery") else None
    if payload.incident_type == "FAILED_ATTEMPT":
        row.status = "failed_attempt"

        if shipment:
            shipment.status = "failed_attempt"

    else:
        row.status = "incident"

        if shipment:
            shipment.status = "incident"

    if partial_status:
        row.status = partial_status
        if shipment:
            shipment.status = partial_status
    row.version += 1

    db.commit()

    return {"id": str(incident.id), "incident_type": incident.incident_type, "status": incident.resolution_status}
