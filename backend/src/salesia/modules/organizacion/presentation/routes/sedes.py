from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import salesia.modules.organizacion.application.sedes as service_sedes
from salesia.modules.organizacion.application.contracts.sedes import BranchCreateModel, BranchUpdateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/branches")
def list_branches(
    is_active: Optional[bool] = Query(default=None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service_sedes.list_branches(is_active=is_active, current_user=current_user, db=db)


@router.post("/branches", status_code=201)
def create_branch(
    req: BranchCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("organization:manage")),
    db: Session = Depends(get_db),
):
    return service_sedes.create_branch(req=req, current_user=current_user, db=db)


@router.patch("/branches/{branch_id}")
def update_branch(
    branch_id: UUID,
    req: BranchUpdateModel,
    current_user: AuthenticatedUser = Depends(require_permission("organization:manage")),
    db: Session = Depends(get_db),
):
    return service_sedes.update_branch(branch_id=branch_id, req=req, current_user=current_user, db=db)
