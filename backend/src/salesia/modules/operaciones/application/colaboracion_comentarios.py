import json
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application.auxiliares.now import now
from salesia.modules.operaciones.application.auxiliares.related_exists import related_exists
from salesia.modules.operaciones.application.auxiliares.sanitize_html import sanitize_html
from salesia.modules.operaciones.application.contracts.colaboracion_comentarios import (
    CommentCreateRequest,
    CommentUpdateRequest,
)
from salesia.modules.operaciones.infrastructure_models import CollaborationComment
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.domain.roles import ROLE_PERMISSIONS_MAP, SystemRole
from salesia.shared.infrastructure.errors import DomainForbiddenException
from salesia.shared.infrastructure.models import UserModel


def create_comment(payload: CommentCreateRequest, current_user: AuthenticatedUser, db: Session):
    if not related_exists(db, current_user, payload.resource_type, payload.resource_id):
        raise HTTPException(422, "El recurso relacionado no existe en esta empresa.")

    sanitized = sanitize_html(payload.content)

    authorized_mentions = []

    blocked_mentions = []

    perm_map = {"customer": "customers:read", "product": "products:read", "sale": "sales:read"}

    needed_perm = perm_map.get(payload.resource_type)

    for user_id in payload.mentions:
        target_user = db.scalar(
            select(UserModel).where(
                UserModel.id == user_id, UserModel.company_id == current_user.company_id, UserModel.is_active.is_(True)
            )
        )

        if not target_user:
            blocked_mentions.append(str(user_id))

            continue

        user_role = SystemRole(target_user.role) if target_user.role in [r.value for r in SystemRole] else None

        user_perms = {p.value for p in ROLE_PERMISSIONS_MAP.get(user_role, set())} if user_role else set()

        if needed_perm and needed_perm not in user_perms and target_user.role != "company_admin":
            blocked_mentions.append(str(user_id))

        else:
            authorized_mentions.append(str(user_id))

    comment = CollaborationComment(
        company_id=current_user.company_id,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        author_id=current_user.user_id,
        content=payload.content,
        sanitized_content=sanitized,
        mentions_json=json.dumps(authorized_mentions),
        version=1,
        created_at=now(),
        updated_at=now(),
    )

    db.add(comment)

    db.commit()

    return {
        "id": str(comment.id),
        "resource_type": comment.resource_type,
        "resource_id": str(comment.resource_id),
        "content": comment.sanitized_content,
        "author_id": str(comment.author_id),
        "authorized_mentions": authorized_mentions,
        "blocked_mentions": blocked_mentions,
        "created_at": comment.created_at.isoformat(),
    }


def list_comments(resource_type: str, resource_id: UUID, current_user: AuthenticatedUser, db: Session):
    if not related_exists(db, current_user, resource_type, resource_id):
        raise HTTPException(422, "El recurso relacionado no existe.")

    rows = db.scalars(
        select(CollaborationComment)
        .where(
            CollaborationComment.company_id == current_user.company_id,
            CollaborationComment.resource_type == resource_type,
            CollaborationComment.resource_id == resource_id,
        )
        .order_by(CollaborationComment.created_at)
    ).all()

    return {
        "items": [
            {
                "id": str(r.id),
                "content": r.sanitized_content,
                "author_id": str(r.author_id),
                "version": r.version,
                "is_edited": r.is_edited,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
    }


def update_comment(comment_id: UUID, payload: CommentUpdateRequest, current_user: AuthenticatedUser, db: Session):
    comment = db.scalar(
        select(CollaborationComment)
        .where(CollaborationComment.id == comment_id, CollaborationComment.company_id == current_user.company_id)
        .with_for_update()
    )

    if not comment:
        raise HTTPException(404, "Comentario no encontrado.")

    if comment.author_id != current_user.user_id and current_user.role != "company_admin":
        raise DomainForbiddenException("No tiene permiso para editar este comentario.")

    comment.content = payload.content

    comment.sanitized_content = sanitize_html(payload.content)

    comment.version += 1

    comment.is_edited = True

    comment.updated_at = now()

    db.commit()

    return {
        "id": str(comment.id),
        "content": comment.sanitized_content,
        "version": comment.version,
        "updated_at": comment.updated_at.isoformat(),
    }
