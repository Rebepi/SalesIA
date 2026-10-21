from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from salesia.modules.finanzas.application import liquidaciones_devolucion as service
from salesia.modules.finanzas.application.reembolsos import refund_options
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(tags=["Liquidación de devoluciones"])


@router.get("/refund-options/{payment_id}")
def get_refund_options(payment_id: UUID, user: AuthenticatedUser = Depends(require_permission("payments:read")), db: Session = Depends(get_db)):
    return refund_options(payment_id, user, db)


@router.get("/return-settlements")
def return_settlements(search: str | None = Query(None, max_length=128), limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0), user: AuthenticatedUser = Depends(require_permission("payments:read")), db: Session = Depends(get_db)):
    return service.list_settlements(db, user, search, limit, offset)


@router.get("/return-settlements/{return_id}")
def get_return_settlement(return_id: UUID, user: AuthenticatedUser = Depends(require_permission("payments:read")), db: Session = Depends(get_db)):
    return service.settlement_data(db, user, service.scoped_return(db, user, return_id))


@router.post("/return-settlements/{return_id}/store-credit")
def grant_return_store_credit(return_id: UUID, payload: service.StoreCreditRequest, user: AuthenticatedUser = Depends(require_permission("payments:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.grant_store_credit(db, user, return_id, payload, key)


@router.post("/return-settlements/{return_id}/settle-debt")
def settle_return_debt(return_id: UUID, payload: service.SettlementRequest, user: AuthenticatedUser = Depends(require_permission("payments:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.settle_debt(db, user, return_id, payload, key)
