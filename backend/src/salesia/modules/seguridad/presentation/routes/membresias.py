from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.seguridad.application.membresias as service_membresias
from salesia.modules.seguridad.application.contracts.membresias import InvitationRequest, MembershipUpdateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/memberships/invitations", status_code=201)
def invite_member(
    req: InvitationRequest,
    current_user: AuthenticatedUser = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
):
    return service_membresias.invite_member(req=req, current_user=current_user, db=db)


@router.post("/memberships/invitations/{membership_id}/resend")
def resend_invitation(
    membership_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
):
    return service_membresias.resend_invitation(membership_id=membership_id, current_user=current_user, db=db)


@router.delete("/memberships/invitations/{membership_id}")
def cancel_invitation(
    membership_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
):
    return service_membresias.cancel_invitation(membership_id=membership_id, current_user=current_user, db=db)


@router.patch("/memberships/{membership_id}")
def update_membership(
    membership_id: UUID,
    req: MembershipUpdateModel,
    current_user: AuthenticatedUser = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
):
    return service_membresias.update_membership(
        membership_id=membership_id, req=req, current_user=current_user, db=db
    )


@router.post("/memberships/{membership_id}/transfer-admin")
def transfer_admin(
    membership_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
):
    return service_membresias.transfer_admin(membership_id=membership_id, current_user=current_user, db=db)
