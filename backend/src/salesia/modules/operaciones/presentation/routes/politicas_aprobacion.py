from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application import politicas_aprobacion as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.modules.seguridad.infrastructure.sessions import permissions_for
from salesia.shared.infrastructure.database import get_db
from salesia.shared.infrastructure.models import UserModel

router = APIRouter(prefix="/business")


@router.get("/approval-policies")
def list_approval_policies(user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db)):
    return service.list_policies(db, user)


@router.put("/approval-policies")
def save_approval_policy(payload: service.ApprovalPolicyRequest, user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.save_policy(db, user, payload, key)


@router.get("/approval-members")
def list_approval_members(user: AuthenticatedUser = Depends(require_permission("organization:manage", "approvals:manage")), db: Session = Depends(get_db)):
    members = db.scalars(select(UserModel).where(UserModel.company_id == user.company_id, UserModel.is_active.is_(True)).order_by(UserModel.email)).all()
    return [{"id": str(member.id), "name": member.email} for member in members if "approvals:manage" in permissions_for(db, member)]


@router.get("/approval-delegations")
def list_approval_delegations(user: AuthenticatedUser = Depends(require_permission("organization:manage", "approvals:manage")), db: Session = Depends(get_db)):
    return service.list_delegations(db, user)


@router.post("/approval-delegations", status_code=201)
def create_approval_delegation(payload: service.DelegationRequest, user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.create_delegation(db, user, payload, key)


@router.post("/approval-delegations/{identifier}/revoke")
def revoke_approval_delegation(identifier: UUID, user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db)):
    return service.revoke_delegation(db, user, identifier)
