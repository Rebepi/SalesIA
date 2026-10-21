from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from salesia.modules.inventario.application import reclamos_proveedor as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(tags=["Reclamos y compensaciones de proveedores"])


@router.get("/supplier-claim-sources")
def supplier_claim_sources(kind: service.SourceKind, limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0), user: AuthenticatedUser = Depends(require_permission("purchases:read")), db: Session = Depends(get_db)):
    return service.source_options(db, user, kind, limit, offset)


@router.get("/supplier-claims")
def list_supplier_claims(status: Literal["open", "acknowledged", "credit_available", "partially_compensated", "resolved", "rejected", "cancelled"] | None = None, supplier_id: UUID | None = None, limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0), user: AuthenticatedUser = Depends(require_permission("purchases:read", "payments:read")), db: Session = Depends(get_db)):
    return service.list_claims(db, user, status, supplier_id, limit, offset)


@router.post("/supplier-claims", status_code=201)
def create_supplier_claim(payload: service.ClaimCreateRequest, user: AuthenticatedUser = Depends(require_permission("purchases:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.create_claim(db, user, payload, key)


@router.get("/supplier-claims/{claim_id}")
def get_supplier_claim(claim_id: UUID, user: AuthenticatedUser = Depends(require_permission("purchases:read", "payments:read")), db: Session = Depends(get_db)):
    return service.serialize_claim(db, user, service.scoped_claim(db, user, claim_id, False))


@router.post("/supplier-claims/{claim_id}/acknowledge")
def acknowledge_supplier_claim(claim_id: UUID, payload: service.ClaimAcknowledgeRequest, user: AuthenticatedUser = Depends(require_permission("purchases:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.acknowledge_claim(db, user, claim_id, payload, key)


@router.post("/supplier-claims/{claim_id}/credits", status_code=201)
def register_supplier_claim_credit(claim_id: UUID, payload: service.ClaimCreditRequest, user: AuthenticatedUser = Depends(require_permission("payments:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.issue_claim_credit(db, user, claim_id, payload, key)


@router.post("/supplier-claims/{claim_id}/replacement-orders", status_code=201)
def create_supplier_claim_replacement(claim_id: UUID, payload: service.ClaimReplacementRequest, user: AuthenticatedUser = Depends(require_permission("purchases:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.create_replacement_order(db, user, claim_id, payload, key)


@router.post("/supplier-claims/{claim_id}/{action}")
def change_supplier_claim(claim_id: UUID, action: Literal["cancel", "reject", "reopen"], payload: service.ClaimActionRequest, user: AuthenticatedUser = Depends(require_permission("purchases:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.claim_action(db, user, claim_id, action, payload, key)
