from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.colaboracion_comentarios as service_colaboracion_comentarios
from salesia.modules.operaciones.application.contracts.colaboracion_comentarios import (
    CommentCreateRequest,
    CommentUpdateRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/collaboration/comments", status_code=201)
def create_comment(
    payload: CommentCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_colaboracion_comentarios.create_comment(payload=payload, current_user=current_user, db=db)


@router.get("/collaboration/comments")
def list_comments(
    resource_type: str,
    resource_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_colaboracion_comentarios.list_comments(
        resource_type=resource_type, resource_id=resource_id, current_user=current_user, db=db
    )


@router.put("/collaboration/comments/{comment_id}")
def update_comment(
    comment_id: UUID,
    payload: CommentUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_colaboracion_comentarios.update_comment(
        comment_id=comment_id, payload=payload, current_user=current_user, db=db
    )
