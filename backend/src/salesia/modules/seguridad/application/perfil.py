from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.seguridad.application.contracts.perfil import ProfileUpdateRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.infrastructure.sessions import permissions_for
from salesia.shared.infrastructure.errors import DomainNotFoundException
from salesia.shared.infrastructure.models import UserModel


def get_me(current_user: AuthenticatedUser):
    return {**current_user.model_dump(), "is_active": True}


def get_profile(current_user: AuthenticatedUser, db: Session):
    user = db.scalar(
        select(UserModel).where(UserModel.id == current_user.user_id, UserModel.company_id == current_user.company_id)
    )
    if not user:
        raise DomainNotFoundException("Usuario no encontrado.")
    return {
        "user_id": str(user.id),
        "company_id": str(user.company_id),
        "full_name": user.full_name or "",
        "email": user.email,
        "phone": user.phone or "",
        "role": user.role,
        "permissions": permissions_for(db, user),
        "mfa_enabled": user.mfa_enabled,
        "ui_theme": user.ui_theme,
        "ui_density": user.ui_density,
        "reduced_motion": user.reduced_motion,
        "font_scale": user.font_scale,
        "contrast_mode": user.contrast_mode,
        "default_page_size": user.default_page_size,
        "sidebar_mode": user.sidebar_mode,
        "accessible_tables": user.accessible_tables,
        "toast_position": user.toast_position,
    }


def update_profile(payload: ProfileUpdateRequest, current_user: AuthenticatedUser, db: Session):
    user = db.scalar(
        select(UserModel)
        .where(UserModel.id == current_user.user_id, UserModel.company_id == current_user.company_id)
        .with_for_update()
    )
    if not user:
        raise DomainNotFoundException("Usuario no encontrado.")
    if payload.full_name is not None:
        user.full_name = payload.full_name.strip() if payload.full_name else None
    if payload.phone is not None:
        user.phone = payload.phone.strip() if payload.phone else None
    if payload.ui_theme is not None:
        user.ui_theme = payload.ui_theme
    if payload.ui_density is not None:
        user.ui_density = payload.ui_density
    if payload.reduced_motion is not None:
        user.reduced_motion = payload.reduced_motion
    if payload.font_scale is not None:
        user.font_scale = payload.font_scale
    if payload.contrast_mode is not None:
        user.contrast_mode = payload.contrast_mode
    if payload.default_page_size is not None:
        user.default_page_size = payload.default_page_size
    if payload.sidebar_mode is not None:
        user.sidebar_mode = payload.sidebar_mode
    if payload.accessible_tables is not None:
        user.accessible_tables = payload.accessible_tables
    if payload.toast_position is not None:
        user.toast_position = payload.toast_position
    db.commit()
    return {
        "user_id": str(user.id),
        "full_name": user.full_name or "",
        "email": user.email,
        "phone": user.phone or "",
        "role": user.role,
        "mfa_enabled": user.mfa_enabled,
        "ui_theme": user.ui_theme,
        "ui_density": user.ui_density,
        "reduced_motion": user.reduced_motion,
        "font_scale": user.font_scale,
        "contrast_mode": user.contrast_mode,
        "default_page_size": user.default_page_size,
        "sidebar_mode": user.sidebar_mode,
        "accessible_tables": user.accessible_tables,
        "toast_position": user.toast_position,
    }
