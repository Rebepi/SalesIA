import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.catalogo.service import validate_unit_fraction
from salesia.modules.inventario.infrastructure_models import DeliveryShipment, ProofOfDelivery
from salesia.modules.inventario.service import document
from salesia.modules.operaciones.infrastructure_models import CollaborationTask
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.shared.infrastructure.models import ProductModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request

RESULT_STATES = ("dispatched", "in_transit", "out_for_delivery", "incident", "failed_attempt", "partially_delivered", "pending_redelivery")


class DeliveryResultLine(BaseModel):
    product_id: UUID
    accepted_quantity: Decimal = Field(ge=0, max_digits=20, decimal_places=6)
    rejected_quantity: Decimal = Field(ge=0, max_digits=20, decimal_places=6)
    pending_quantity: Decimal = Field(ge=0, max_digits=20, decimal_places=6)
    rejected_action: Literal["redelivery", "return"] = "redelivery"
    reason: str = Field(default="", max_length=2000)


class DeliveryResultRequest(BaseModel):
    version: int = Field(ge=1)
    received_by_name: str = Field(min_length=2, max_length=255)
    received_by_id_doc: str | None = Field(default=None, max_length=64)
    outside_window_reason: str = Field(default="", max_length=2000)
    notes: str = Field(min_length=5, max_length=4000)
    items: list[DeliveryResultLine] = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def unique_items(self):
        if len({item.product_id for item in self.items}) != len(self.items):
            raise ValueError("Cada producto debe aparecer una sola vez en el resultado de entrega.")
        return self


def result_lines(db, user, row):
    details = json.loads(row.details_json or "{}")
    stored = {item["product_id"]: item for item in details.get("delivery_outcome", [])}
    results = []
    for line in row.lines:
        product = db.scalar(select(ProductModel).where(ProductModel.company_id == user.company_id, ProductModel.id == line.product_id))
        previous = stored.get(str(line.product_id), {})
        accepted = Decimal(previous.get("accepted_quantity", str(line.quantity) if row.status == "delivered" else "0"))
        rejected = Decimal(previous.get("return_quantity", "0"))
        pending = max(Decimal("0"), line.quantity - accepted - rejected)
        results.append({"product_id": str(line.product_id), "name": product.name if product else "Producto histórico", "sku": product.sku if product else "", "transported_quantity": str(line.quantity if row.status != "ready" else Decimal("0")), "planned_quantity": str(line.quantity), "accepted_quantity": str(accepted), "return_quantity": str(rejected), "pending_quantity": str(pending), "reason": previous.get("reason", "")})
    return results


def result_data(db, user, row):
    details = json.loads(row.details_json or "{}")
    identifiers = [UUID(value) for value in details.get("delivery_followup_tasks", {}).values()]
    tasks = db.scalars(select(CollaborationTask).where(CollaborationTask.company_id == user.company_id, CollaborationTask.id.in_(identifiers))).all() if identifiers else []
    from salesia.modules.inventario.application.ventanas_entrega import reservation_data, reservation_for_delivery
    return {"window_reservation": reservation_data(db, user, reservation_for_delivery(db, user, row.id)), "id": str(row.id), "status": row.status, "version": row.version, "items": result_lines(db, user, row), "attempts": details.get("delivery_attempts", []), "tasks": [{"id": str(task.id), "title": task.title, "status": task.status} for task in tasks], "business_date": business_date(db, user.company_id).isoformat()}


def update_task(db, user, row, details, kind, quantities, notes):
    links = details.setdefault("delivery_followup_tasks", {})
    task_id = links.get(kind)
    task = db.scalar(select(CollaborationTask).where(CollaborationTask.company_id == user.company_id, CollaborationTask.id == UUID(task_id))) if task_id else None
    needed = any(Decimal(item["quantity"]) > 0 for item in quantities)
    if not needed:
        if task and kind == "redelivery" and task.status not in ("done", "cancelled"):
            task.status, task.resolution_notes, task.version = "done", "Las cantidades pendientes fueron aceptadas o derivadas a devolución mediante el resultado de entrega.", task.version + 1
        return
    description = "\n".join(f'{item["name"]}: {item["quantity"]}' for item in quantities if Decimal(item["quantity"]) > 0)
    text = f"{notes}\n{description}\nEntrega {row.id}. " + ("Programar un nuevo intento para estas unidades que siguen bajo custodia logística." if kind == "redelivery" else "Recibir físicamente las unidades rechazadas y resolver su disposición y ajuste comercial. Registrar rechazo no devuelve existencias ni emite notas de crédito.")
    if task is None:
        shipment = db.scalar(select(DeliveryShipment).where(DeliveryShipment.company_id == user.company_id, DeliveryShipment.delivery_document_id == row.id))
        task = CollaborationTask(company_id=user.company_id, title=f'{"Reentrega" if kind == "redelivery" else "Devolución logística"} {str(row.id)[:8].upper()}', description=text, creator_id=user.user_id, assignee_id=user.user_id, resource_type="delivery", resource_id=shipment.id if shipment else row.id, status="pending", priority="high", version=1)
        db.add(task)
        db.flush()
        links[kind] = str(task.id)
    else:
        task.description, task.status, task.resolution_notes, task.version = text, "pending", None, task.version + 1


def record_result(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"delivery.result:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    row = document(db, user, "DELIVERY", identifier)
    if row.version != payload.version or row.status not in RESULT_STATES:
        raise HTTPException(409, "La entrega cambió o no tiene mercancía en tránsito pendiente de resolver.")
    if db.scalar(select(ProofOfDelivery.id).where(ProofOfDelivery.company_id == user.company_id, ProofOfDelivery.delivery_id == row.id)):
        raise HTTPException(409, "La entrega ya tiene conformidad total. Las devoluciones posteriores siguen su circuito comercial.")
    from salesia.modules.inventario.application.ventanas_entrega import validate_acceptance, complete_reservation, reservation_for_delivery
    window_reservation = validate_acceptance(db, user, row, payload.received_by_name, payload.received_by_id_doc, payload.outside_window_reason) if any(item.accepted_quantity > 0 for item in payload.items) else reservation_for_delivery(db, user, row.id, True)
    lines = {UUID(item["product_id"]): item for item in result_lines(db, user, row)}
    if set(lines) != {item.product_id for item in payload.items}:
        raise HTTPException(422, "Declara el resultado de todos los productos, incluidos los ya resueltos con cantidades nuevas iguales a cero.")
    stored, redelivery, returns = [], [], []
    for item in payload.items:
        original = lines[item.product_id]
        pending = Decimal(original["pending_quantity"])
        if item.accepted_quantity + item.rejected_quantity + item.pending_quantity != pending:
            raise HTTPException(422, f'El resultado de {original["name"]} debe repartir exactamente el saldo pendiente {pending}.')
        if (item.rejected_quantity > 0 or item.pending_quantity > 0) and len(item.reason.strip()) < 5:
            raise HTTPException(422, "Explica el motivo de cada rechazo o cantidad pendiente con al menos cinco caracteres.")
        product = db.scalar(select(ProductModel).where(ProductModel.company_id == user.company_id, ProductModel.id == item.product_id))
        for amount in (item.accepted_quantity, item.rejected_quantity, item.pending_quantity):
            if amount > 0:
                validate_unit_fraction(db, user.company_id, product.unit_of_measure, amount)
        accepted = Decimal(original["accepted_quantity"]) + item.accepted_quantity
        rejected = Decimal(original["return_quantity"]) + (item.rejected_quantity if item.rejected_action == "return" else Decimal("0"))
        remaining = pending - item.accepted_quantity - (item.rejected_quantity if item.rejected_action == "return" else Decimal("0"))
        stored.append({"product_id": str(item.product_id), "accepted_quantity": str(accepted), "return_quantity": str(rejected), "reason": item.reason or original["reason"]})
        redelivery.append({"name": original["name"], "quantity": str(remaining)})
        returns.append({"name": original["name"], "quantity": str(rejected)})
    details = json.loads(row.details_json or "{}")
    details["delivery_outcome"] = stored
    attempts = details.setdefault("delivery_attempts", [])
    attempts.append({"at": datetime.now(timezone.utc).isoformat(), "actor": user.email, "received_by_name": payload.received_by_name, "received_by_id_doc": payload.received_by_id_doc, "notes": payload.notes, "items": payload.model_dump(mode="json")["items"]})
    pending = sum((Decimal(item["quantity"]) for item in redelivery), Decimal("0"))
    returning = sum((Decimal(item["quantity"]) for item in returns), Decimal("0"))
    accepted = sum((Decimal(item["accepted_quantity"]) for item in stored), Decimal("0"))
    row.status = "partially_delivered" if pending > 0 and accepted > 0 else "pending_redelivery" if pending > 0 else "partially_rejected" if returning > 0 and accepted > 0 else "rejected" if returning > 0 else "delivered"
    row.version += 1
    complete_reservation(db, user, window_reservation, row)
    update_task(db, user, row, details, "redelivery", redelivery, payload.notes)
    update_task(db, user, row, details, "return", returns, payload.notes)
    shipment = db.scalar(select(DeliveryShipment).where(DeliveryShipment.company_id == user.company_id, DeliveryShipment.delivery_document_id == row.id))
    if shipment:
        shipment.status = row.status
        shipment.delivered_at = datetime.now(timezone.utc) if row.status == "delivered" else None
    if row.status == "delivered":
        db.add(ProofOfDelivery(company_id=user.company_id, delivery_id=row.id, received_by_name=payload.received_by_name, received_by_id_doc=payload.received_by_id_doc, delivered_at=datetime.now(timezone.utc), notes=payload.notes, created_by=user.user_id))
    row.details_json = json.dumps(details)
    db.flush()
    result = result_data(db, user, row)
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="RECORD_DELIVERY_RESULT", entity_type="DeliveryShipment", entity_id=shipment.id if shipment else row.id, diff={"status": row.status, "version": row.version, "items": stored, "tasks": details.get("delivery_followup_tasks", {})})
    complete_request(record, result)
    db.commit()
    return result


def full_acceptance(db, user, row, received_by_name, notes, received_by_id_doc=None, outside_window_reason=""):
    from salesia.modules.inventario.application.ventanas_entrega import validate_acceptance
    window_reservation = validate_acceptance(db, user, row, received_by_name, received_by_id_doc, outside_window_reason)
    lines = result_lines(db, user, row)
    if any(Decimal(item["return_quantity"]) > 0 for item in lines):
        raise HTTPException(409, "La entrega tiene unidades rechazadas para devolución. Conserva su resultado parcial y resuelve la devolución; no registres una conformidad total.")
    details = json.loads(row.details_json or "{}")
    details["delivery_outcome"] = [{"product_id": item["product_id"], "accepted_quantity": item["planned_quantity"], "return_quantity": "0", "reason": item["reason"]} for item in lines]
    details.setdefault("delivery_attempts", []).append({"at": datetime.now(timezone.utc).isoformat(), "actor": user.email, "received_by_name": received_by_name, "received_by_id_doc": received_by_id_doc, "notes": notes, "items": [{"product_id": item["product_id"], "accepted_quantity": item["pending_quantity"], "rejected_quantity": "0", "pending_quantity": "0"} for item in lines]})
    update_task(db, user, row, details, "redelivery", [], notes)
    row.details_json = json.dumps(details)
    return window_reservation
