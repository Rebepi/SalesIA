from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from salesia.modules.finanzas.application import custodia as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/cash-custody", tags=["Custodia y traspasos de efectivo"])


@router.get("/options")
def cash_custody_options(user: AuthenticatedUser = Depends(require_permission("cash:register:manage")), db: Session = Depends(get_db)):
    return service.options(db, user)


@router.post("/accounts", status_code=201)
def create_custody_account(payload: service.AccountRequest, user: AuthenticatedUser = Depends(require_permission("cash:register:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.save_account(db, user, None, payload, key)


@router.put("/accounts/{account_id}")
def update_custody_account(account_id: UUID, payload: service.AccountRequest, user: AuthenticatedUser = Depends(require_permission("cash:register:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.save_account(db, user, account_id, payload, key)


@router.get("/transfers")
def custody_transfers(status: Literal["sent", "disputed", "return_pending", "received", "returned"] | None = None, currency: str | None = Query(None, pattern=r"^[A-Z]{3}$"), limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0), user: AuthenticatedUser = Depends(require_permission("cash:register:manage")), db: Session = Depends(get_db)):
    return service.list_transfers(db, user, status, currency, limit, offset)


@router.post("/transfers", status_code=201)
def create_custody_transfer(payload: service.TransferRequest, user: AuthenticatedUser = Depends(require_permission("cash:register:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.create_transfer(db, user, payload, key)


@router.get("/transfers/{transfer_id}")
def get_custody_transfer(transfer_id: UUID, user: AuthenticatedUser = Depends(require_permission("cash:register:manage")), db: Session = Depends(get_db)):
    return service.transfer_data(db, user, service.scoped(db, user, service.CashCustodyTransferModel, transfer_id))


@router.post("/transfers/{transfer_id}/actions")
def act_on_custody_transfer(transfer_id: UUID, payload: service.TransferAction, user: AuthenticatedUser = Depends(require_permission("cash:register:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.transfer_action(db, user, transfer_id, payload, key)
