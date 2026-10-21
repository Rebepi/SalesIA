import json
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.finanzas.application.auxiliares.serialize_return import _serialize_return
from salesia.modules.finanzas.application.configuracion import WITHOUT_RECEIPT_LIMIT
from salesia.modules.finanzas.application.contracts.devoluciones_sin_comprobante import ReturnWithoutReceiptRequest
from salesia.modules.finanzas.infrastructure_models import ReturnLineModel, ReturnModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainForbiddenException
from salesia.shared.infrastructure.models import CustomerModel, WarehouseModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def create_return_without_receipt(
    payload: ReturnWithoutReceiptRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: str
):
    if "company_admin" not in current_user.role and "admin" not in current_user.role:
        if payload.manual_valuation_total > WITHOUT_RECEIPT_LIMIT:
            raise HTTPException(
                403, f"Un vendedor no puede procesar devoluciones sin comprobante por mas de {WITHOUT_RECEIPT_LIMIT}."
            )

    record, cached = claim_request(
        db,
        current_user.company_id,
        "returns.without_receipt",
        idempotency_key,
        {
            "customer_id": str(payload.customer_id),
            "reason": payload.reason,
            "amount": str(payload.manual_valuation_total),
        },
    )

    if cached is not None:
        return cached

    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.id == payload.customer_id, CustomerModel.company_id == current_user.company_id
        )
    )

    if not cust:
        other = db.scalar(select(CustomerModel.id).where(CustomerModel.id == payload.customer_id))

        if other:
            raise DomainForbiddenException("Cliente de otra empresa no permitido.")

        raise HTTPException(404, "Cliente no encontrado.")

    wh = db.scalar(
        select(WarehouseModel).where(
            WarehouseModel.id == payload.warehouse_id,
            WarehouseModel.company_id == current_user.company_id,
            WarehouseModel.is_active.is_(True),
        )
    )

    if not wh:
        raise HTTPException(422, "Almacen no encontrado o de otra empresa.")

    ret = ReturnModel(
        id=uuid4(),
        company_id=current_user.company_id,
        sale_id=None,
        customer_id=payload.customer_id,
        warehouse_id=payload.warehouse_id,
        status="requested",
        reason=payload.reason,
        is_without_receipt=True,
        manual_valuation_total=payload.manual_valuation_total,
        requested_by=current_user.user_id,
        evidence_urls_json=json.dumps([]),
    )

    db.add(ret)

    db.flush()

    for item in payload.items:
        db.add(
            ReturnLineModel(
                id=uuid4(),
                return_id=ret.id,
                product_id=item.product_id,
                quantity=item.quantity,
                disposition=item.disposition,
            )
        )

    complete_request(record, _serialize_return(ret))

    db.commit()

    return _serialize_return(ret)
