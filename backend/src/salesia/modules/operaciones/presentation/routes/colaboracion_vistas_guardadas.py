from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.colaboracion_vistas_guardadas as service_colaboracion_vistas_guardadas
from salesia.modules.operaciones.application.contracts.colaboracion_vistas_guardadas import (
    SavedViewCreateRequest,
    SavedViewUpdateRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/collaboration/saved-views", status_code=201)
def create_saved_view(
    payload: SavedViewCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_colaboracion_vistas_guardadas.create_saved_view(payload=payload, current_user=current_user, db=db)


@router.get("/collaboration/saved-views")
def list_saved_views(
    resource_type: str, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_colaboracion_vistas_guardadas.list_saved_views(
        resource_type=resource_type, current_user=current_user, db=db
    )


@router.put("/collaboration/saved-views/{view_id}")
def update_saved_view(
    view_id: UUID,
    payload: SavedViewUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_colaboracion_vistas_guardadas.update_saved_view(
        view_id=view_id, payload=payload, current_user=current_user, db=db
    )


@router.delete("/collaboration/saved-views/{view_id}")
def delete_saved_view(
    view_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_colaboracion_vistas_guardadas.delete_saved_view(view_id=view_id, current_user=current_user, db=db)
