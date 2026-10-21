from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import salesia.modules.seguridad.application.roles as service_roles
from salesia.modules.seguridad.application.contracts.roles import RoleCloneModel, RoleCreateModel, RoleUpdateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/roles")
def list_roles(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service_roles.list_roles(current_user=current_user, db=db)


@router.get("/roles/compare")
def compare_roles(
    source: str, target: str, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service_roles.compare_roles(source=source, target=target, current_user=current_user, db=db)


@router.post("/roles/{source_role}/clone", status_code=201)
def clone_role(
    source_role: str,
    req: RoleCloneModel,
    current_user: AuthenticatedUser = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
):
    return service_roles.clone_role(source_role=source_role, req=req, current_user=current_user, db=db)


@router.post("/roles", status_code=201)
def create_custom_role(
    req: RoleCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
):
    return service_roles.create_custom_role(req=req, current_user=current_user, db=db)


@router.get("/roles/{role_key}/impact")
def custom_role_impact(
    role_key: str,
    current_user: AuthenticatedUser = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
):
    return service_roles.custom_role_impact(role_key=role_key, current_user=current_user, db=db)


@router.patch("/roles/{role_key}")
def update_custom_role(
    role_key: str,
    payload: RoleUpdateModel,
    current_user: AuthenticatedUser = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
):
    return service_roles.update_custom_role(role_key=role_key, payload=payload, current_user=current_user, db=db)


@router.delete("/roles/{role_key}")
def delete_custom_role(
    role_key: str,
    affected_users: int = Query(ge=0),
    replacement_role: Optional[str] = None,
    current_user: AuthenticatedUser = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
):
    return service_roles.delete_custom_role(
        role_key=role_key,
        affected_users=affected_users,
        replacement_role=replacement_role,
        current_user=current_user,
        db=db,
    )
