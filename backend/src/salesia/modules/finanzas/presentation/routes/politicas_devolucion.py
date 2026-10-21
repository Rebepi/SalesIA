from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from salesia.modules.finanzas.application import politicas_devolucion as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/return-policy", tags=["Políticas de devolución"])


@router.get("")
def get_return_policy(user: AuthenticatedUser = Depends(require_permission("sales:read")), db: Session = Depends(get_db)):
    return {**service.policy_data(db, user.company_id), "can_manage": "organization:manage" in user.permissions}


@router.put("")
def save_return_policy(payload: service.PolicySave, user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.save_policy(db, user, payload, key)


@router.get("/history")
def return_policy_history(user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db)):
    return service.policy_history(db, user.company_id)
