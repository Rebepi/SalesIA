import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.inventario.application.auxiliares.validate_carrier_url import validate_carrier_url
from salesia.modules.inventario.application.contracts.comunes import StockLine
from salesia.modules.inventario.application.contracts.entregas_operaciones import (
    DeliveryCompleteRequest,
    DeliveryCreateRequest,
    DeliveryInterceptRequest,
)
from salesia.modules.inventario.infrastructure_models import (
    DeliveryIncident,
    DeliveryShipment,
    DeliveryTrackingEvent,
    ProofOfDelivery,
    SupplyDocument,
    SupplyLine,
)
from salesia.modules.inventario.service import create_document, document, move_stock, release_reservation, response
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import SaleModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def create_delivery(
    payload: DeliveryCreateRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: Optional[str]
):
    record, cached = None, None

    if idempotency_key:
        record, cached = claim_request(
            db, current_user.company_id, "delivery.create", idempotency_key, payload.model_dump(mode="json")
        )

        if cached is not None:
            return cached

    sale = db.scalar(
        select(SaleModel).where(
            SaleModel.id == payload.sale_id,
            SaleModel.company_id == current_user.company_id,
            SaleModel.status.in_(("confirmed", "paid")),
        )
    )

    if not sale or sale.warehouse_id != payload.warehouse_id:
        raise HTTPException(409, "La venta no está confirmada o el almacén no coincide.")

    validate_carrier_url(payload.tracking_url)

    sale_lines = {l.product_id: l for l in sale.lines}

    if not sale_lines:
        raise HTTPException(422, "La venta no contiene líneas para entregar.")

    existing_dispatches = db.scalars(
        select(SupplyLine)
        .join(SupplyDocument, SupplyDocument.id == SupplyLine.document_id)
        .where(
            SupplyDocument.company_id == current_user.company_id,
            SupplyDocument.sale_id == sale.id,
            SupplyDocument.kind == "DELIVERY",
            SupplyDocument.status != "cancelled",
        )
    ).all()

    already_dispatched = {}

    for line in existing_dispatches:
        already_dispatched[line.product_id] = already_dispatched.get(line.product_id, Decimal("0")) + line.quantity

    items_to_deliver = payload.items or [
        StockLine(
            product_id=l.product_id,
            quantity=l.quantity,
            unit_cost=getattr(l, "unit_price_snapshot", getattr(l, "unit_price", Decimal("0"))),
        )
        for l in sale.lines
    ]

    for item in items_to_deliver:
        if item.product_id not in sale_lines:
            raise HTTPException(422, "Producto no presente en la venta.")

        total_planned = already_dispatched.get(item.product_id, Decimal("0")) + item.quantity

        if total_planned > sale_lines[item.product_id].quantity:
            raise HTTPException(409, "La cantidad a despachar supera el saldo elegible de la venta.")

    doc = create_document(
        db,
        current_user,
        "DELIVERY",
        "ready",
        payload.warehouse_id,
        items_to_deliver,
        sale_id=sale.id,
        details_json=json.dumps({"carrier": payload.carrier, "tracking_number": payload.tracking_number}),
    )

    shipment = DeliveryShipment(
        id=uuid4(),
        company_id=current_user.company_id,
        delivery_document_id=doc.id,
        sale_id=sale.id,
        recipient_name=payload.recipient_name,
        delivery_address=payload.delivery_address,
        recipient_phone=payload.recipient_phone,
        carrier=payload.carrier,
        tracking_number=payload.tracking_number,
        tracking_url=payload.tracking_url,
        shipping_fee_charged=payload.shipping_fee_charged,
        logistics_cost=payload.logistics_cost,
        estimated_delivery_date=payload.estimated_delivery_date,
        is_guaranteed=payload.is_guaranteed,
        status="ready",
        notes=payload.notes,
    )

    db.add(shipment)

    db.flush()

    res = response(doc)

    res["shipment"] = {
        "recipient_name": shipment.recipient_name,
        "delivery_address": shipment.delivery_address,
        "carrier": shipment.carrier,
        "tracking_number": shipment.tracking_number,
        "shipping_fee_charged": str(shipment.shipping_fee_charged),
        "logistics_cost": str(shipment.logistics_cost),
        "estimated_delivery_date": shipment.estimated_delivery_date.isoformat()
        if shipment.estimated_delivery_date
        else None,
        "is_guaranteed": shipment.is_guaranteed,
    }

    if record:
        complete_request(record, res)

    db.commit()

    return res


def list_deliveries(
    status: Optional[str],
    warehouse_id: Optional[UUID],
    carrier: Optional[str],
    delayed_only: bool,
    limit: int,
    offset: int,
    current_user: AuthenticatedUser,
    db: Session,
):
    query = select(SupplyDocument).where(
        SupplyDocument.company_id == current_user.company_id, SupplyDocument.kind == "DELIVERY"
    )

    if status:
        query = query.where(SupplyDocument.status == status)

    if warehouse_id:
        query = query.where(SupplyDocument.warehouse_id == warehouse_id)

    docs = db.scalars(query.order_by(SupplyDocument.created_at.desc())).all()

    results = []

    now = datetime.now(timezone.utc)

    for doc in docs:
        shipment = db.scalar(select(DeliveryShipment).where(DeliveryShipment.delivery_document_id == doc.id))

        est_date = shipment.estimated_delivery_date if shipment else None

        if est_date and est_date.tzinfo is None:
            est_date = est_date.replace(tzinfo=timezone.utc)

        is_delayed = bool(doc.status != "delivered" and est_date and est_date < now)

        delayed_days = (now - est_date).days if is_delayed and est_date else 0

        if delayed_only and not is_delayed:
            continue

        if carrier and shipment and shipment.carrier != carrier:
            continue

        next_action = (
            "DISPATCH"
            if doc.status == "ready"
            else "RECORD_POD"
            if doc.status in ("dispatched", "in_transit", "out_for_delivery")
            else "RESOLVE_INCIDENT"
            if doc.status in ("failed_attempt", "incident", "partially_delivered", "pending_redelivery", "partially_rejected", "rejected")
            else "NONE"
        )

        results.append(
            {
                "id": str(doc.id),
                "status": doc.status,
                "warehouse_id": str(doc.warehouse_id),
                "sale_id": str(doc.sale_id) if doc.sale_id else None,
                "carrier": shipment.carrier if shipment else None,
                "tracking_number": shipment.tracking_number if shipment else None,
                "tracking_url": shipment.tracking_url if shipment else None,
                "recipient_name": shipment.recipient_name if shipment else None,
                "delivery_address": shipment.delivery_address if shipment else None,
                "shipping_fee_charged": str(shipment.shipping_fee_charged) if shipment else "0.000000",
                "logistics_cost": str(shipment.logistics_cost) if shipment else "0.000000",
                "estimated_delivery_date": est_date.isoformat() if est_date else None,
                "is_guaranteed": shipment.is_guaranteed if shipment else False,
                "is_delayed": is_delayed,
                "delayed_days": delayed_days,
                "next_action": next_action,
                "created_at": doc.created_at.isoformat(),
            }
        )

    paginated = results[offset : offset + limit]

    return {"items": paginated, "count": len(results), "delayed_count": sum(1 for r in results if r["is_delayed"])}


def get_delivery(delivery_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = document(db, current_user, "DELIVERY", delivery_id)

    shipment = db.scalar(
        select(DeliveryShipment).where(
            DeliveryShipment.delivery_document_id == delivery_id, DeliveryShipment.company_id == current_user.company_id
        )
    )

    events = db.scalars(
        select(DeliveryTrackingEvent)
        .where(
            DeliveryTrackingEvent.delivery_id == delivery_id,
            DeliveryTrackingEvent.company_id == current_user.company_id,
        )
        .order_by(DeliveryTrackingEvent.occurred_at.asc())
    ).all()

    incidents = db.scalars(
        select(DeliveryIncident)
        .where(DeliveryIncident.delivery_id == delivery_id, DeliveryIncident.company_id == current_user.company_id)
        .order_by(DeliveryIncident.created_at.asc())
    ).all()

    pod = db.scalar(
        select(ProofOfDelivery).where(
            ProofOfDelivery.delivery_id == delivery_id, ProofOfDelivery.company_id == current_user.company_id
        )
    )

    res = response(row)

    res["shipment"] = {
        "recipient_name": shipment.recipient_name if shipment else None,
        "delivery_address": shipment.delivery_address if shipment else None,
        "recipient_phone": shipment.recipient_phone if shipment else None,
        "carrier": shipment.carrier if shipment else None,
        "tracking_number": shipment.tracking_number if shipment else None,
        "tracking_url": shipment.tracking_url if shipment else None,
        "shipping_fee_charged": str(shipment.shipping_fee_charged) if shipment else "0.000000",
        "logistics_cost": str(shipment.logistics_cost) if shipment else "0.000000",
        "estimated_delivery_date": shipment.estimated_delivery_date.isoformat()
        if shipment and shipment.estimated_delivery_date
        else None,
        "is_guaranteed": shipment.is_guaranteed if shipment else False,
        "dispatched_at": shipment.dispatched_at.isoformat() if shipment and shipment.dispatched_at else None,
        "delivered_at": shipment.delivered_at.isoformat() if shipment and shipment.delivered_at else None,
    }

    res["tracking_events"] = [
        {
            "event_code": e.event_code,
            "event_status": e.event_status,
            "description": e.description,
            "location": e.location,
            "occurred_at": e.occurred_at.isoformat(),
        }
        for e in events
    ]

    res["incidents"] = [
        {"incident_type": inc.incident_type, "description": inc.description, "resolution_status": inc.resolution_status}
        for inc in incidents
    ]

    from salesia.modules.inventario.application.entregas_parciales import result_data
    res["delivery_result"] = result_data(db, current_user, row)
    res["has_proof_of_delivery"] = pod is not None

    return res


def dispatch_delivery(delivery_id: UUID, current_user: AuthenticatedUser, db: Session, idempotency_key: Optional[str]):
    record, cached = None, None

    if idempotency_key:
        record, cached = claim_request(
            db, current_user.company_id, "delivery.dispatch", idempotency_key, {"delivery_id": str(delivery_id)}
        )

        if cached is not None:
            return cached

    row = document(db, current_user, "DELIVERY", delivery_id)

    if row.status == "dispatched":
        res = response(row)

        if record:
            complete_request(record, res)

            db.commit()

        return res

    if row.status != "ready":
        raise HTTPException(409, "La entrega no está lista para despacho.")

    shipment = db.scalar(
        select(DeliveryShipment).where(
            DeliveryShipment.delivery_document_id == delivery_id, DeliveryShipment.company_id == current_user.company_id
        )
    )

    for line in row.lines:
        move_stock(
            db,
            row.company_id,
            row.warehouse_id,
            line.product_id,
            -line.quantity,
            line.unit_cost,
            row.id,
            "DESPACHO_VENTA",
        )

        line.processed_quantity = line.quantity

    row.status = "dispatched"

    row.version += 1

    if shipment:
        shipment.status = "dispatched"

        shipment.dispatched_at = datetime.now(timezone.utc)

    res = response(row)

    if record:
        complete_request(record, res)

    db.commit()

    return res


def cancel_delivery(delivery_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = document(db, current_user, "DELIVERY", delivery_id)

    if row.status != "ready":
        raise HTTPException(409, "No se puede cancelar una entrega ya despachada sin procedimiento de intercepción.")

    row.status = "cancelled"

    row.version += 1

    shipment = db.scalar(
        select(DeliveryShipment).where(
            DeliveryShipment.delivery_document_id == delivery_id, DeliveryShipment.company_id == current_user.company_id
        )
    )

    if shipment:
        shipment.status = "cancelled"

    for line in row.lines:
        release_reservation(db, current_user.company_id, "DELIVERY", row.id, line.product_id)

    from salesia.modules.inventario.application.ventanas_entrega import cancel_for_delivery
    cancel_for_delivery(db, current_user, row)
    db.commit()

    return {"id": str(row.id), "status": "cancelled"}


def intercept_delivery(
    delivery_id: UUID, payload: DeliveryInterceptRequest, current_user: AuthenticatedUser, db: Session
):
    row = document(db, current_user, "DELIVERY", delivery_id)

    if row.status not in ("dispatched", "in_transit", "out_for_delivery"):
        raise HTTPException(409, "Solo se pueden interceptar entregas en tránsito.")

    row.status = "intercept_requested"

    row.version += 1

    shipment = db.scalar(
        select(DeliveryShipment).where(
            DeliveryShipment.delivery_document_id == delivery_id, DeliveryShipment.company_id == current_user.company_id
        )
    )

    if shipment:
        shipment.status = "intercept_requested"

    db.commit()

    return {"id": str(row.id), "status": "intercept_requested"}


def complete_delivery(
    delivery_id: UUID, payload: DeliveryCompleteRequest, current_user: AuthenticatedUser, db: Session
):
    row = document(db, current_user, "DELIVERY", delivery_id)

    from salesia.modules.inventario.application.entregas_parciales import RESULT_STATES, full_acceptance
    if row.status not in RESULT_STATES:
        raise HTTPException(409, "Solo se pueden marcar entregadas órdenes previamente despachadas.")

    window_reservation = full_acceptance(db, current_user, row, payload.received_by_name, payload.proof_of_delivery, payload.received_by_id_doc, payload.outside_window_reason)
    row.status = "delivered"
    from salesia.modules.inventario.application.ventanas_entrega import complete_reservation
    complete_reservation(db, current_user, window_reservation, row)

    row.version += 1

    row.details_json = json.dumps({**json.loads(row.details_json or "{}"), **payload.model_dump()})

    shipment = db.scalar(
        select(DeliveryShipment).where(
            DeliveryShipment.delivery_document_id == delivery_id, DeliveryShipment.company_id == current_user.company_id
        )
    )

    if shipment:
        shipment.status = "delivered"

        shipment.delivered_at = datetime.now(timezone.utc)

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
            delivered_at=datetime.now(timezone.utc),
            notes=payload.proof_of_delivery,
            created_by=current_user.user_id,
        )

        db.add(pod)

    db.commit()

    return response(row)
