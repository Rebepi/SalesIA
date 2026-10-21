from typing import Literal
from uuid import UUID
from salesia.modules.finanzas.application.acuerdos_cobranza import AgreementChange, change_agreement

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

import salesia.modules.finanzas.application.cuentas_cobrar as service_cuentas_cobrar
from salesia.modules.finanzas.application.contracts.cuentas_cobrar import CollectionActivityRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/receivables")
def get_receivables(
    current_user: AuthenticatedUser = Depends(require_permission("payments:read")), db: Session = Depends(get_db)
):

    return service_cuentas_cobrar.get_receivables(current_user=current_user, db=db)


@router.get("/receivables/{sale_id}/context")
def receivable_context(
    sale_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("payments:read")),
    db: Session = Depends(get_db),
):

    return service_cuentas_cobrar.receivable_context(sale_id=sale_id, current_user=current_user, db=db)


@router.post("/receivables/{sale_id}/activities", status_code=201)
def create_collection_activity(
    sale_id: UUID,
    payload: CollectionActivityRequest,
    current_user: AuthenticatedUser = Depends(require_permission("payments:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_cuentas_cobrar.create_collection_activity(
        sale_id=sale_id, payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/receivables/{sale_id}/agreements/{agreement_id}/{action}")
def change_collection_agreement(sale_id: UUID, agreement_id: UUID, action: Literal["renegotiate", "cancel"], payload: AgreementChange, current_user: AuthenticatedUser = Depends(require_permission("payments:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return change_agreement(db, current_user, sale_id, agreement_id, action, payload, key)
