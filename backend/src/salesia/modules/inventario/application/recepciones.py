import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.inventario.application.contracts.recepciones import LandedCostRequest
from salesia.modules.inventario.infrastructure_models import LandedCostAdjustment
from salesia.modules.inventario.receipt_workflow import GoodsReceiptCreateRequest, receive_purchase
from salesia.modules.inventario.service import document, record_audit
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import InventoryStockModel, KardexMovementModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def create_goods_receipt(
    payload: GoodsReceiptCreateRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: str
):
    record, cached = claim_request(
        db, current_user.company_id, "goods_receipt.create", idempotency_key, payload.model_dump(mode="json")
    )

    if cached is not None:
        return cached

    result = receive_purchase(db, current_user, payload)

    complete_request(record, result)

    db.commit()

    return result


def add_landed_cost(
    receipt_id: UUID,
    payload: LandedCostRequest,
    current_user: AuthenticatedUser,
    db: Session,
    idempotency_key: Optional[str],
):
    record = None

    if idempotency_key:
        record, cached = claim_request(
            db,
            current_user.company_id,
            "purchase.landed_cost",
            idempotency_key,
            {"receipt_id": str(receipt_id), **payload.model_dump(mode="json")},
        )

        if cached is not None:
            return cached

    receipt = document(db, current_user, "GOODS_RECEIPT", receipt_id)

    inspections = json.loads(receipt.details_json or "{}").get("inspections", [])

    eligible_ids = {
        UUID(item["product_id"])
        for item in inspections
        if item["status"] == "accepted" or item.get("resolution") == "RESTOCK"
    }

    eligible_lines = (
        [line for line in receipt.lines if line.product_id in eligible_ids]
        if inspections
        else (list(receipt.lines) if receipt.status == "accepted" else [])
    )

    if not eligible_lines:
        raise HTTPException(409, "Solo se pueden prorratear costos sobre artículos aceptados de una recepción.")

    total_charges = sum(c.amount for c in payload.charges)

    total_receipt_value = sum(l.quantity * l.unit_cost for l in eligible_lines)

    total_receipt_qty = sum(l.quantity for l in eligible_lines)

    for c in payload.charges:
        adj = LandedCostAdjustment(
            id=uuid4(),
            company_id=current_user.company_id,
            goods_receipt_id=receipt.id,
            charge_type=c.charge_type,
            amount=c.amount,
            allocation_method=c.allocation_method,
            notes=c.notes,
            created_by=current_user.user_id,
        )

        db.add(adj)

    for line in eligible_lines:
        if line.quantity <= 0:
            continue

        line_charge = Decimal("0")

        for c in payload.charges:
            if c.allocation_method == "VALUE" and total_receipt_value > 0:
                line_charge += c.amount * ((line.quantity * line.unit_cost) / total_receipt_value)

            elif c.allocation_method == "QUANTITY" and total_receipt_qty > 0:
                line_charge += c.amount * (line.quantity / total_receipt_qty)

        additional_unit_cost = (line_charge / line.quantity).quantize(Decimal("0.000001"))

        line.unit_cost += additional_unit_cost

        stock = db.scalar(
            select(InventoryStockModel)
            .where(
                InventoryStockModel.company_id == current_user.company_id,
                InventoryStockModel.warehouse_id == receipt.warehouse_id,
                InventoryStockModel.product_id == line.product_id,
            )
            .with_for_update()
        )

        if stock and stock.physical_quantity > 0:
            stock.average_cost = (
                (stock.physical_quantity * stock.average_cost + line_charge) / stock.physical_quantity
            ).quantize(Decimal("0.000001"))

            db.add(
                KardexMovementModel(
                    id=uuid4(),
                    company_id=current_user.company_id,
                    warehouse_id=receipt.warehouse_id,
                    product_id=line.product_id,
                    movement_type="AJUSTE_VALORIZACION",
                    reference_doc_type="LANDED_COST",
                    reference_doc_id=receipt.id,
                    quantity_delta=Decimal("0.000000"),
                    resulting_physical_qty=stock.physical_quantity,
                    unit_cost=line.unit_cost,
                    moving_average_cost=stock.average_cost,
                    occurred_at=datetime.now(timezone.utc),
                )
            )

    result = {
        "receipt_id": str(receipt.id),
        "total_charges_applied": str(total_charges),
        "lines": [{"product_id": str(l.product_id), "new_unit_cost": str(l.unit_cost)} for l in receipt.lines],
    }

    record_audit(
        db,
        current_user,
        receipt.id,
        "ALLOCATE_PURCHASE_COST",
        {"total_charges": str(total_charges), "eligible_lines": len(eligible_lines)},
    )

    if record is not None:
        complete_request(record, result)

    db.commit()

    return result
