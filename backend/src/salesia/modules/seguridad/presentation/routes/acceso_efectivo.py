from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from salesia.modules.seguridad.application import acceso_efectivo as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/memberships")


@router.get("/{membership_id}/effective-access")
def member_effective_access(membership_id: UUID, proposed_role: str | None = None, user: AuthenticatedUser = Depends(require_permission("users:manage")), db: Session = Depends(get_db)):
    return service.member_access(db, user, membership_id, proposed_role)
