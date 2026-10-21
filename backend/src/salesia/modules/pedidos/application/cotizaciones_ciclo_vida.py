import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.infrastructure_models import ProductProfileModel
from salesia.modules.pedidos.application.auxiliares.audit import audit
from salesia.modules.pedidos.application.auxiliares.build_order import build_order
from salesia.modules.pedidos.application.auxiliares.now import now
from salesia.modules.pedidos.application.auxiliares.order_response import order_response
from salesia.modules.pedidos.application.auxiliares.price_lines import price_lines
from salesia.modules.pedidos.application.auxiliares.quotation_response import quotation_response
from salesia.modules.pedidos.application.auxiliares.validate_references import validate_references
from salesia.modules.pedidos.application.contracts.cotizaciones_ciclo_vida import (
    AcceptQuotationRequest,
    QuotationVersionModel,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainForbiddenException
from salesia.shared.infrastructure.models import InventoryStockModel, ProductModel, QuotationModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def create_quotation_version(
    quotation_id: UUID, req: QuotationVersionModel, current_user: AuthenticatedUser, db: Session, idempotency_key: str
):
    record, cached = claim_request(
        db, current_user.company_id, f"quotations.version:{quotation_id}", idempotency_key, req.model_dump(mode="json")
    )

    if cached is not None:
        return cached

    previous = db.scalar(
        select(QuotationModel)
        .where(QuotationModel.id == quotation_id, QuotationModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not previous:
        raise HTTPException(404, "Cotización no encontrada.")

    if previous.status not in ("pending", "accepted") or previous.converted_order_id:
        raise HTTPException(409, "La cotización ya no admite nuevas versiones.")

    lines, subtotal, tax, total = price_lines(db, current_user.company_id, req.lines)

    row = QuotationModel(
        company_id=previous.company_id,
        branch_id=previous.branch_id,
        customer_id=previous.customer_id,
        quotation_number=previous.quotation_number,
        version=previous.version + 1,
        status="pending",
        currency=previous.currency,
        subtotal_amount=subtotal,
        tax_amount=tax,
        total_amount=total,
        valid_until=req.valid_until.isoformat() if req.valid_until else previous.valid_until,
        payment_terms_days=previous.payment_terms_days,
        delivery_terms=req.delivery_terms or previous.delivery_terms,
        notes=req.notes or previous.notes,
        special_conditions=req.special_conditions
        if req.special_conditions is not None
        else previous.special_conditions,
        seller_id=req.seller_id or previous.seller_id,
        lines_json=json.dumps(lines),
    )

    previous.status = "superseded"

    db.add(row)

    db.flush()

    audit(
        db,
        current_user,
        "VERSION",
        "Quotation",
        row.id,
        {"previous_version_id": str(previous.id), "previous_version": previous.version},
    )

    response = quotation_response(row)

    complete_request(record, response)

    db.commit()

    return response


def accept_quotation(
    quotation_id: UUID,
    req: Optional[AcceptQuotationRequest],
    current_user: AuthenticatedUser,
    db: Session,
    idempotency_key: str,
):
    body = req.model_dump(mode="json") if req else {}

    record, cached = claim_request(
        db, current_user.company_id, f"quotations.accept:{quotation_id}", idempotency_key, body
    )

    if cached is not None:
        return cached

    row = db.scalar(
        select(QuotationModel)
        .where(QuotationModel.id == quotation_id, QuotationModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not row:
        raise HTTPException(404, "Cotización no encontrada.")

    if row.status not in ("pending", "negotiating"):
        raise HTTPException(409, "Solo una cotización pendiente puede aceptarse.")

    if row.valid_until and datetime.fromisoformat(row.valid_until).astimezone(timezone.utc) < now():
        raise HTTPException(409, "La cotización ha expirado.")

    row.status = "accepted"

    row.accepted_at = now()

    audit(
        db,
        current_user,
        "ACCEPT",
        "Quotation",
        row.id,
        {"accepted_by": current_user.email, "conditions": req.conditions if req else None},
    )

    response = quotation_response(row)

    complete_request(record, response)

    db.commit()

    return response


def convert_quotation_to_order(
    quotation_id: UUID,
    warehouse_id: UUID,
    honor_expired_price: bool,
    current_user: AuthenticatedUser,
    db: Session,
    idempotency_key: str,
):
    record, cached = claim_request(
        db,
        current_user.company_id,
        f"quotations.convert:{quotation_id}",
        idempotency_key,
        {"warehouse_id": str(warehouse_id), "honor_expired_price": honor_expired_price},
    )

    if cached is not None:
        return cached

    quotation = db.scalar(
        select(QuotationModel)
        .where(QuotationModel.id == quotation_id, QuotationModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not quotation:
        other = db.scalar(select(QuotationModel.id).where(QuotationModel.id == quotation_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Cotización no encontrada.")

    if quotation.converted_order_id or quotation.status != "accepted":
        raise HTTPException(409, "La cotización no es elegible para conversión.")

    if (
        quotation.valid_until
        and datetime.fromisoformat(quotation.valid_until).astimezone(timezone.utc) < now()
        and not honor_expired_price
    ):
        raise HTTPException(409, "La cotización ha vencido; revalide precios.")

    if not quotation.branch_id:
        raise HTTPException(422, "La cotización necesita una sucursal.")

    validate_references(db, current_user.company_id, quotation.customer_id, quotation.branch_id, warehouse_id)

    quotation_lines = json.loads(quotation.lines_json)

    unavailable = []

    for line in quotation_lines:
        product_id = UUID(str(line["product_id"]))

        profile = db.scalar(
            select(ProductProfileModel).where(
                ProductProfileModel.company_id == current_user.company_id, ProductProfileModel.product_id == product_id
            )
        )

        if profile and (profile.product_type == "service" or not profile.track_inventory):
            continue

        stock = db.scalar(
            select(InventoryStockModel).where(
                InventoryStockModel.company_id == current_user.company_id,
                InventoryStockModel.warehouse_id == warehouse_id,
                InventoryStockModel.product_id == product_id,
            )
        )

        available = (stock.physical_quantity - stock.reserved_quantity) if stock else Decimal("0")

        requested = Decimal(str(line["quantity"]))

        if available < requested:
            product = db.scalar(
                select(ProductModel).where(
                    ProductModel.company_id == current_user.company_id, ProductModel.id == product_id
                )
            )

            unavailable.append(
                {
                    "sku": product.sku if product else str(line["product_id"]),
                    "requested": str(requested),
                    "available": str(available),
                }
            )

    if unavailable:
        raise HTTPException(
            409,
            {
                "message": "El almacén seleccionado no tiene existencias suficientes para convertir la cotización.",
                "unavailable": unavailable,
            },
        )

    order = build_order(
        db,
        current_user,
        quotation.customer_id,
        quotation.branch_id,
        warehouse_id,
        quotation.currency,
        quotation.payment_terms_days,
        quotation_lines,
        quotation.subtotal_amount,
        quotation.tax_amount,
        quotation.total_amount,
        quotation.id,
        delivery_terms=quotation.delivery_terms,
    )

    quotation.converted_order_id, quotation.status = order.id, "converted"

    response = order_response(order)

    complete_request(record, response)

    db.commit()

    return response
