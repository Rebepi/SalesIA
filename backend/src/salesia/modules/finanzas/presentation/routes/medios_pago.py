from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import salesia.modules.finanzas.application.medios_pago as service_medios_pago
from salesia.modules.finanzas.application.contracts.medios_pago import (
    PaymentMethodCreateRequest,
    PaymentMethodUpdateRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/payment-methods")
def list_payment_methods(
    current_user: AuthenticatedUser = Depends(require_permission("payments:read")), db: Session = Depends(get_db)
):

    return service_medios_pago.list_payment_methods(current_user=current_user, db=db)


@router.post("/payment-methods", status_code=status.HTTP_201_CREATED)
def create_payment_method(
    payload: PaymentMethodCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("payments:write")),
    db: Session = Depends(get_db),
):

    return service_medios_pago.create_payment_method(payload=payload, current_user=current_user, db=db)


@router.patch("/payment-methods/{method_id}")
def update_payment_method(
    method_id: UUID,
    payload: PaymentMethodUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("payments:write")),
    db: Session = Depends(get_db),
):

    return service_medios_pago.update_payment_method(
        method_id=method_id, payload=payload, current_user=current_user, db=db
    )
