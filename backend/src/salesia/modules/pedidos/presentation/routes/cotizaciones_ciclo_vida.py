from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

import salesia.modules.pedidos.application.cotizaciones_ciclo_vida as service_cotizaciones_ciclo_vida
from salesia.modules.pedidos.application.contracts.cotizaciones_ciclo_vida import (
    AcceptQuotationRequest,
    QuotationVersionModel,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/quotations/{quotation_id}/versions", status_code=201)
def create_quotation_version(
    quotation_id: UUID,
    req: QuotationVersionModel,
    current_user: AuthenticatedUser = Depends(require_permission("quotations:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_cotizaciones_ciclo_vida.create_quotation_version(
        quotation_id=quotation_id, req=req, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/quotations/{quotation_id}/accept")
def accept_quotation(
    quotation_id: UUID,
    req: Optional[AcceptQuotationRequest] = None,
    current_user: AuthenticatedUser = Depends(require_permission("quotations:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_cotizaciones_ciclo_vida.accept_quotation(
        quotation_id=quotation_id, req=req, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/quotations/{quotation_id}/convert", status_code=201)
def convert_quotation_to_order(
    quotation_id: UUID,
    warehouse_id: UUID = Query(...),
    honor_expired_price: bool = Query(default=False),
    current_user: AuthenticatedUser = Depends(require_permission("quotations:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_cotizaciones_ciclo_vida.convert_quotation_to_order(
        quotation_id=quotation_id,
        warehouse_id=warehouse_id,
        honor_expired_price=honor_expired_price,
        current_user=current_user,
        db=db,
        idempotency_key=idempotency_key,
    )
