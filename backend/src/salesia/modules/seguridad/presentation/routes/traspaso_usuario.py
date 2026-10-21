from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from salesia.modules.seguridad.application import traspaso_usuario as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/memberships/{membership_id}/handover")


@router.get("")
def user_handover_preview(membership_id: UUID, user: AuthenticatedUser = Depends(require_permission("users:manage")), db: Session = Depends(get_db)):
    return service.preflight(db, user, membership_id)


@router.get("/options")
def user_handover_options(membership_id: UUID, group: str, search: str | None = None, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), user: AuthenticatedUser = Depends(require_permission("users:manage")), db: Session = Depends(get_db)):
    service.member(db, user.company_id, membership_id)
    return service.candidates(db, user, membership_id, group, search, limit, offset)


@router.post("/transfer")
def transfer_user_responsibilities(membership_id: UUID, payload: service.HandoverRequest, user: AuthenticatedUser = Depends(require_permission("users:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.execute(db, user, membership_id, payload, key)


@router.post("/suspend")
def suspend_user_after_handover(membership_id: UUID, payload: service.HandoverRequest, user: AuthenticatedUser = Depends(require_permission("users:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.execute(db, user, membership_id, payload, key, True)
