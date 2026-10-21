import json
from collections import defaultdict
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.pedidos.application.auxiliares.locked_order import locked_order
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.modules.ventas.application.contracts.ventas_operaciones import CreateSaleDraftRequest, LineItemRequest
from salesia.modules.ventas.application.ventas_operaciones import create_draft
from salesia.modules.ventas.infrastructure.models import SaleModel
from salesia.shared.infrastructure.database import get_db

router = APIRouter()


class BillingLineRequest(BaseModel):
    order_line_number: int = Field(ge=1)
    quantity: Decimal = Field(gt=0)


class OrderBillingRequest(BaseModel):
    document_type: Literal["INVOICE", "RECEIPT"] = "RECEIPT"
    is_credit: bool = False
    exchange_rate: Decimal = Field(default=Decimal("1"), gt=0)
    lines: list[BillingLineRequest] = Field(min_length=1, max_length=500)


@router.get("/orders/{order_id}/billing")
def order_billing_options(order_id: UUID, current_user: AuthenticatedUser = Depends(require_permission("sales:read")), db: Session = Depends(get_db)):
    order = locked_order(db, current_user, order_id)
    sales = db.scalars(select(SaleModel).where(SaleModel.company_id == current_user.company_id, SaleModel.order_id == order.id).order_by(SaleModel.created_at)).all()
    billed = defaultdict(lambda: Decimal("0"))
    for sale in sales:
        if sale.status in ("draft", "confirmed", "paid", "refunded"):
            for line in sale.lines:
                billed[line.order_line_number] += line.quantity
    lines = []
    for number, line in enumerate(json.loads(order.lines_json), 1):
        remaining = max(Decimal("0"), Decimal(line["quantity"]) - Decimal(line.get("cancelled_quantity", "0")) - billed[number])
        lines.append({**line, "order_line_number": number, "billed_quantity": str(billed[number]), "billable_quantity": str(remaining)})
    return {"order_id": str(order.id), "currency": order.currency, "lines": lines, "sales": [{"sale_id": str(sale.id), "number": f"{sale.series}-{sale.number:08d}", "status": sale.status, "fulfillment_status": sale.fulfillment_status, "total": str(sale.total_amount)} for sale in sales]}


@router.post("/orders/{order_id}/billing", status_code=201)
def create_order_invoice(order_id: UUID, payload: OrderBillingRequest, current_user: AuthenticatedUser = Depends(require_permission("sales:write")), db: Session = Depends(get_db), idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    order = locked_order(db, current_user, order_id)
    originals = {number: line for number, line in enumerate(json.loads(order.lines_json), 1)}
    requested = []
    numbers = set()
    for item in payload.lines:
        original = originals.get(item.order_line_number)
        if original is None or item.order_line_number in numbers:
            raise HTTPException(422, "Selecciona cada línea del pedido una sola vez.")
        numbers.add(item.order_line_number)
        requested.append(LineItemRequest(product_id=original["product_id"], sku=original["sku"], product_name=original.get("product_name") or original.get("name") or original["sku"], quantity=item.quantity, unit_price=Decimal(original.get("unit_price", "0")), order_line_number=item.order_line_number))
    request = CreateSaleDraftRequest(order_id=order.id, customer_id=order.customer_id, branch_id=order.branch_id, warehouse_id=order.warehouse_id, currency=order.currency, payment_terms_days=order.payment_terms_days, document_type=payload.document_type, is_credit=payload.is_credit, exchange_rate=payload.exchange_rate, lines=requested)
    return create_draft(request, current_user, db, idempotency_key)
