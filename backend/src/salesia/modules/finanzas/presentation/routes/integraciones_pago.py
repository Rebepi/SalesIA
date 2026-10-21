from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.orm import Session

import salesia.modules.finanzas.application.integraciones_pago as service_integraciones_pago
from salesia.modules.finanzas.application.contracts.integraciones_pago import (
    IntegrationCreateRequest,
    PaymentIntentConfirmRequest,
    PaymentIntentCreateRequest,
    PaymentIntentSyncRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


webhook_router = APIRouter(prefix="")


@router.post("/payment-connections", status_code=201)
def create_payment_connection(
    payload: IntegrationCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("payments:write")),
    db: Session = Depends(get_db),
):

    return service_integraciones_pago.create_payment_connection(payload=payload, current_user=current_user, db=db)


@router.post("/payment-connections/{connection_id}/rotate-secret")
def rotate_payment_connection_secret(
    connection_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("payments:write")),
    db: Session = Depends(get_db),
):

    return service_integraciones_pago.rotate_payment_connection_secret(
        connection_id=connection_id, current_user=current_user, db=db
    )


@webhook_router.post("/webhooks/payments/{connection_id}")
async def payment_webhook(
    connection_id: UUID,
    request: Request,
    x_webhook_signature: Optional[str] = Header(None),
    x_webhook_timestamp: Optional[int] = Header(None),
    x_webhook_event_id: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):

    return await service_integraciones_pago.payment_webhook(
        connection_id=connection_id,
        request=request,
        x_webhook_signature=x_webhook_signature,
        x_webhook_timestamp=x_webhook_timestamp,
        x_webhook_event_id=x_webhook_event_id,
        db=db,
    )


@router.post("/payment-intents", status_code=status.HTTP_201_CREATED)
def create_payment_intent(
    payload: PaymentIntentCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("payments:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_integraciones_pago.create_payment_intent(
        payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.get("/payment-intents/{intent_id}")
def get_payment_intent(
    intent_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("payments:read")),
    db: Session = Depends(get_db),
):

    return service_integraciones_pago.get_payment_intent(intent_id=intent_id, current_user=current_user, db=db)


@router.post("/payment-intents/{intent_id}/confirm")
def confirm_payment_intent(
    intent_id: UUID,
    payload: PaymentIntentConfirmRequest,
    current_user: AuthenticatedUser = Depends(require_permission("payments:write")),
    db: Session = Depends(get_db),
):

    return service_integraciones_pago.confirm_payment_intent(
        intent_id=intent_id, payload=payload, current_user=current_user, db=db
    )


@router.post("/payment-intents/{intent_id}/sync-status")
def sync_payment_intent_status(
    intent_id: UUID,
    payload: PaymentIntentSyncRequest,
    current_user: AuthenticatedUser = Depends(require_permission("payments:write")),
    db: Session = Depends(get_db),
):

    return service_integraciones_pago.sync_payment_intent_status(
        intent_id=intent_id, payload=payload, current_user=current_user, db=db
    )
