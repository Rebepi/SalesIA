from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from salesia.modules.finanzas.application import caja_chica as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/petty-cash", tags=["Caja chica y rendiciones"])


@router.get("/options")
def petty_cash_options(user: AuthenticatedUser = Depends(require_permission("cash:register:manage")), db: Session = Depends(get_db)):
    return service.options(db, user)


@router.post("/funds", status_code=201)
def create_petty_cash_fund(payload: service.FundSave, user: AuthenticatedUser = Depends(require_permission("cash:register:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.save_fund(db, user, None, payload, key)


@router.put("/funds/{fund_id}")
def update_petty_cash_fund(fund_id: UUID, payload: service.FundSave, user: AuthenticatedUser = Depends(require_permission("cash:register:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.save_fund(db, user, fund_id, payload, key)


@router.get("/advances")
def petty_cash_advances(status: str | None = Query(None, max_length=32), fund_id: UUID | None = None, limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0), user: AuthenticatedUser = Depends(require_permission("cash:register:manage")), db: Session = Depends(get_db)):
    return service.list_advances(db, user, status, fund_id, limit, offset)


@router.post("/advances", status_code=201)
def request_petty_cash_advance(payload: service.AdvanceCreate, user: AuthenticatedUser = Depends(require_permission("cash:register:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.create_advance(db, user, payload, key)


@router.get("/advances/{advance_id}")
def get_petty_cash_advance(advance_id: UUID, user: AuthenticatedUser = Depends(require_permission("cash:register:manage")), db: Session = Depends(get_db)):
    return service.advance_data(db, user, service.scoped(db, user, service.PettyCashAdvanceModel, advance_id))


@router.post("/advances/{advance_id}/actions")
def act_on_petty_cash_advance(advance_id: UUID, payload: service.AdvanceAction, user: AuthenticatedUser = Depends(require_permission("cash:register:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.act(db, user, advance_id, payload, key)
