from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.seguridad.application.soporte as service_soporte
from salesia.modules.seguridad.application.contracts.soporte import SupportGrantCreateRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/auth/support/grants", status_code=201)
def create_support_grant(
    req: SupportGrantCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("support:temporary")),
    db: Session = Depends(get_db),
):
    return service_soporte.create_support_grant(req=req, current_user=current_user, db=db)


@router.get("/auth/support/grants")
def list_support_grants(
    current_user: AuthenticatedUser = Depends(require_permission("support:temporary")), db: Session = Depends(get_db)
):
    return service_soporte.list_support_grants(current_user=current_user, db=db)


@router.post("/auth/support/grants/{grant_id}/revoke")
def revoke_support_grant(
    grant_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("support:temporary")),
    db: Session = Depends(get_db),
):
    return service_soporte.revoke_support_grant(grant_id=grant_id, current_user=current_user, db=db)
