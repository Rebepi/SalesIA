from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

import salesia.modules.finanzas.application.devoluciones_sin_comprobante as service_devoluciones_sin_comprobante
from salesia.modules.finanzas.application.contracts.devoluciones_sin_comprobante import ReturnWithoutReceiptRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post(
    "/returns/without-receipt",
    status_code=status.HTTP_201_CREATED,
    operation_id="finance_create_return_without_receipt",
)
def create_return_without_receipt(
    payload: ReturnWithoutReceiptRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_devoluciones_sin_comprobante.create_return_without_receipt(
        payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )
