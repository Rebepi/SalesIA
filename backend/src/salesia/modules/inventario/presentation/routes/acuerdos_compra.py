from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from salesia.modules.inventario.application import acuerdos_compra as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(tags=["Acuerdos abiertos de compra"])


@router.get("/purchase-agreements")
def list_purchase_agreements(user: AuthenticatedUser = Depends(require_permission("purchases:read")), db: Session = Depends(get_db)):
    return service.list_agreements(db, user)


@router.post("/purchase-agreements", status_code=201)
def create_purchase_agreement(payload: service.PurchaseAgreementRequest, user: AuthenticatedUser = Depends(require_permission("purchases:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.create_agreement(db, user, payload, key)


@router.post("/purchase-agreements/{agreement_id}/release", status_code=201)
def release_purchase_agreement(agreement_id: UUID, payload: service.AgreementReleaseRequest, user: AuthenticatedUser = Depends(require_permission("purchases:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.release_agreement(db, user, agreement_id, payload, key)


@router.post("/purchase-agreements/{agreement_id}/{action}")
def purchase_agreement_action(agreement_id: UUID, action: Literal["approve", "close"], payload: service.AgreementActionRequest, user: AuthenticatedUser = Depends(require_permission("purchases:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.agreement_action(db, user, agreement_id, action, payload, key)
