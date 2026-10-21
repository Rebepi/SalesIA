import json
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select

from salesia.modules.inventario.infrastructure.models.revisiones import SupplyDocumentRevisionModel
from salesia.modules.inventario.service import document, record_audit, response
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.shared.infrastructure.models import ProductModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def pending_quantity(line):
    return max(Decimal("0"), line.quantity - line.processed_quantity - Decimal(line.cancelled_quantity or 0))


def capture_revision(db, user, order, action, reason):
    db.flush()
    existing = db.scalar(select(SupplyDocumentRevisionModel.id).where(SupplyDocumentRevisionModel.company_id == user.company_id, SupplyDocumentRevisionModel.document_id == order.id, SupplyDocumentRevisionModel.version == order.version))
    if existing:
        return
    snapshot = response(order)
    for line in snapshot["lines"]:
        product = db.scalar(select(ProductModel).where(ProductModel.company_id == user.company_id, ProductModel.id == UUID(line["product_id"])))
        line["sku"] = product.sku if product else ""
        line["name"] = product.name if product else "Producto"
    db.add(SupplyDocumentRevisionModel(company_id=user.company_id, document_id=order.id, version=order.version, actor_id=user.user_id, actor_email=user.email, action=action, reason=reason, snapshot_json=json.dumps(snapshot)))
    db.flush()


class CancelPurchaseLine(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0, max_digits=20, decimal_places=6)


class PurchaseBalanceAction(BaseModel):
    version: int = Field(ge=1)
    action: Literal["cancel_lines", "close_short", "reopen"]
    reason: str = Field(min_length=5, max_length=2000)
    items: list[CancelPurchaseLine] = Field(default_factory=list, max_length=500)

    @model_validator(mode="after")
    def valid_items(self):
        if len({item.product_id for item in self.items}) != len(self.items):
            raise ValueError("Agrupa cada producto en una sola línea.")
        if self.action == "cancel_lines" and not self.items:
            raise ValueError("Selecciona las cantidades pendientes que se cancelarán.")
        if self.action != "cancel_lines" and self.items:
            raise ValueError("El cierre y la reapertura operan sobre el saldo completo.")
        return self


def balance_action(db, user, order_id, payload, key):
    record, cached = claim_request(db, user.company_id, f"purchase.balance:{order_id}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    order = document(db, user, "PURCHASE_ORDER", order_id)
    if order.version != payload.version:
        raise HTTPException(409, "La orden cambió; recarga sus saldos antes de continuar.")
    if order.status not in ("submitted", "reopened") and not ({"purchases:approve", "approvals:manage", "organization:manage"} & set(user.permissions)):
        raise HTTPException(403, "Modificar compromisos aprobados requiere autorización de compras o administración.")
    details = json.loads(order.details_json or "{}")
    before = response(order)
    if payload.action == "reopen":
        if order.status not in ("closed", "cancelled") or not details.get("short_close_cancellations"):
            raise HTTPException(409, "La orden no tiene un cierre de saldo que se pueda reabrir.")
        from salesia.modules.inventario.infrastructure.models.reclamos import SupplierClaimModel
        if db.scalar(select(SupplierClaimModel.id).where(SupplierClaimModel.company_id == user.company_id, SupplierClaimModel.purchase_order_id == order.id, SupplierClaimModel.source_kind == "purchase_order", SupplierClaimModel.reason_type == "shortage", SupplierClaimModel.status.notin_(("cancelled", "rejected")))):
            raise HTTPException(409, "La compra tiene faltantes reclamados al proveedor. Resuelve o cancela el reclamo antes de recuperar las cantidades canceladas.")
        if order.supplier_claim_id:
            from salesia.modules.inventario.application.reclamos_proveedor import replacement_totals, scoped_claim
            claim = scoped_claim(db, user, order.supplier_claim_id)
            if claim.status in ("cancelled", "rejected"):
                raise HTTPException(409, "Reabre primero el reclamo antes de recuperar una reposición cancelada.")
            _, committed, _ = replacement_totals(db, user, claim)
            limits = {UUID(item["product_id"]): Decimal(item["quantity"]) for item in json.loads(claim.items_json)}
            if any(committed[line.product_id] + Decimal(details["short_close_cancellations"].get(str(line.product_id), "0")) > limits.get(line.product_id, Decimal("0")) for line in order.lines):
                raise HTTPException(409, "Las unidades canceladas ya fueron comprometidas en otra reposición del reclamo.")
        restore = details["short_close_cancellations"]
        capture_revision(db, user, order, "BEFORE_REOPEN", "Estado anterior a reapertura")
        for line in order.lines:
            quantity = Decimal(restore.get(str(line.product_id), "0"))
            if quantity > line.cancelled_quantity:
                raise HTTPException(409, "El saldo cancelado no coincide con el cierre histórico.")
            line.cancelled_quantity -= quantity
        details.pop("short_close_cancellations", None)
        order.status = "reopened"
    else:
        if order.status not in ("submitted", "reopened", "approved", "partially_received"):
            raise HTTPException(409, "La orden no admite cancelación de saldo en su estado actual.")
        selected = {item.product_id: item.quantity for item in payload.items}
        known = {line.product_id for line in order.lines}
        if not set(selected) <= known:
            raise HTTPException(422, "La cancelación contiene artículos ajenos a la orden.")
        if payload.action == "close_short":
            selected = {line.product_id: pending_quantity(line) for line in order.lines if pending_quantity(line) > 0}
        if not selected:
            raise HTTPException(409, "No quedan cantidades pendientes de cancelar.")
        for line in order.lines:
            if selected.get(line.product_id, Decimal("0")) > pending_quantity(line):
                raise HTTPException(409, "La cantidad a cancelar supera el saldo pendiente; las unidades recibidas se devuelven mediante su recepción.")
        capture_revision(db, user, order, "BEFORE_CANCEL_BALANCE", "Estado anterior a cancelación de saldo")
        for line in order.lines:
            line.cancelled_quantity += selected.get(line.product_id, Decimal("0"))
        finished = all(pending_quantity(line) == 0 for line in order.lines)
        if finished:
            order.status = "closed" if any(line.processed_quantity > 0 for line in order.lines) else "cancelled"
        if payload.action == "close_short":
            details["short_close_cancellations"] = {str(identifier): str(quantity) for identifier, quantity in selected.items()}
    details.setdefault("balance_history", []).append({"action": payload.action, "reason": payload.reason, "actor": user.email, "date": business_date(db, user.company_id).isoformat(), "version": order.version + 1})
    order.details_json = json.dumps(details)
    order.version += 1
    capture_revision(db, user, order, payload.action.upper(), payload.reason)
    from salesia.modules.inventario.application.reclamos_proveedor import synchronize_replacement_order
    synchronize_replacement_order(db, user, order)
    result = response(order)
    record_audit(db, user, order.id, "PURCHASE_BALANCE_CHANGE", {"reason": payload.reason, "before": before, "after": result})
    complete_request(record, result)
    db.commit()
    return result


def revisions(db, user, order_id):
    document(db, user, "PURCHASE_ORDER", order_id, lock=False)
    rows = db.scalars(select(SupplyDocumentRevisionModel).where(SupplyDocumentRevisionModel.company_id == user.company_id, SupplyDocumentRevisionModel.document_id == order_id).order_by(SupplyDocumentRevisionModel.version)).all()
    return [{"id": str(row.id), "version": row.version, "action": row.action, "reason": row.reason, "actor": row.actor_email, "created_at": row.created_at.isoformat(), "snapshot": json.loads(row.snapshot_json)} for row in rows]
