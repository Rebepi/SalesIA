from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.recepciones as service_recepciones
from salesia.modules.inventario.application.contracts.recepciones import LandedCostRequest
from salesia.modules.inventario.receipt_workflow import GoodsReceiptCreateRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/goods-receipts", status_code=201)
def create_goods_receipt(
    payload: GoodsReceiptCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("purchases:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_recepciones.create_goods_receipt(
        payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/goods-receipts/{receipt_id}/landed-cost", status_code=201)
def add_landed_cost(
    receipt_id: UUID,
    payload: LandedCostRequest,
    current_user: AuthenticatedUser = Depends(require_permission("purchases:write")),
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_recepciones.add_landed_cost(
        receipt_id=receipt_id, payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )
