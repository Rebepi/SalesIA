from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.colaboracion_aprobaciones as service_colaboracion_aprobaciones
from salesia.modules.operaciones.application.contracts.colaboracion_aprobaciones import (
    ApprovalCreateRequest,
    ApprovalDecideRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/collaboration/approvals", status_code=201)
def create_approval(
    payload: ApprovalCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_colaboracion_aprobaciones.create_approval(payload=payload, current_user=current_user, db=db)


@router.get("/collaboration/approvals")
def list_approvals(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):

    return service_colaboracion_aprobaciones.list_approvals(current_user=current_user, db=db)


@router.post("/collaboration/approvals/{approval_id}/decide")
def decide_approval(
    approval_id: UUID,
    payload: ApprovalDecideRequest,
    current_user: AuthenticatedUser = Depends(require_permission("approvals:manage")),
    db: Session = Depends(get_db),
):

    return service_colaboracion_aprobaciones.decide_approval(
        approval_id=approval_id, payload=payload, current_user=current_user, db=db
    )
