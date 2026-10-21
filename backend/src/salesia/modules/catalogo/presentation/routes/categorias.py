from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import salesia.modules.catalogo.application.categorias as service_categorias
from salesia.modules.catalogo.application.contracts.categorias import (
    CategoryCreateModel,
    CategoryRestoreRequest,
    CategoryUpdateModel,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/categories")
def list_categories(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):

    return service_categorias.list_categories(current_user=current_user, db=db)


@router.post("/categories", status_code=status.HTTP_201_CREATED)
def create_category(
    req: CategoryCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_categorias.create_category(req=req, current_user=current_user, db=db)


@router.patch("/categories/{category_id}")
def update_category(
    category_id: UUID,
    req: CategoryUpdateModel,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_categorias.update_category(category_id=category_id, req=req, current_user=current_user, db=db)


@router.get("/categories/{category_id}/impact")
def category_impact(
    category_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("products:read")),
    db: Session = Depends(get_db),
):

    return service_categorias.category_impact(category_id=category_id, current_user=current_user, db=db)


@router.post("/categories/{category_id}/archive")
def archive_category(
    category_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_categorias.archive_category(category_id=category_id, current_user=current_user, db=db)


@router.post("/categories/{category_id}/restore")
def restore_category(
    category_id: UUID,
    payload: CategoryRestoreRequest,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_categorias.restore_category(
        category_id=category_id, payload=payload, current_user=current_user, db=db
    )
