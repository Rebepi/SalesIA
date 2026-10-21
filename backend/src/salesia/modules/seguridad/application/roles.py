import json
import hashlib
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.seguridad.application.auxiliares.ensure_role_delegable import ensure_role_delegable
from salesia.modules.seguridad.application.auxiliares.get_role_permissions import get_role_permissions
from salesia.modules.seguridad.application.auxiliares.role_exists import role_exists
from salesia.modules.seguridad.application.auxiliares.role_title_exists import role_title_exists
from salesia.modules.seguridad.application.contracts.roles import RoleCloneModel, RoleCreateModel, RoleUpdateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.domain.roles import Permission, get_role_catalog
from salesia.modules.seguridad.infrastructure.models import CustomRole
from salesia.modules.seguridad.infrastructure.sessions import revoke_user_sessions
from salesia.shared.infrastructure.errors import DomainConflictException
from salesia.shared.infrastructure.models import CompanyModel, UserModel


def role_impact_hash(role, users):
    return hashlib.sha256(json.dumps({"title": role.title, "description": role.description, "permissions": sorted(json.loads(role.permissions_json)), "users": sorted((str(user.id), user.role, user.is_active) for user in users)}, sort_keys=True).encode()).hexdigest()


def list_roles(current_user: AuthenticatedUser, db: Session):
    roles = [
        {
            "role": r.role.value,
            "title": r.title,
            "description": r.description,
            "permissions": list(r.permissions),
            "is_custom": False,
        }
        for r in get_role_catalog()
        if r.role.value != "platform_admin"
    ]
    roles += [
        {
            "role": r.role_key,
            "title": r.title,
            "description": r.description,
            "permissions": json.loads(r.permissions_json),
            "is_custom": True,
        }
        for r in db.scalars(select(CustomRole).where(CustomRole.company_id == current_user.company_id))
    ]
    permissions = sorted(p.value for p in Permission if p.value != "platform:manage")
    return {
        "total_roles": len(roles),
        "total_permissions": len(permissions),
        "roles": roles,
        "all_permissions": permissions,
    }


def compare_roles(source: str, target: str, current_user: AuthenticatedUser, db: Session):
    source_perms = get_role_permissions(db, current_user.company_id, source)
    target_perms = get_role_permissions(db, current_user.company_id, target)
    if source_perms is None or target_perms is None:
        raise HTTPException(404, "Uno o ambos roles a comparar no existen.")
    s_set = set(source_perms)
    t_set = set(target_perms)
    return {
        "source_role": source,
        "target_role": target,
        "added_permissions": sorted(t_set - s_set),
        "removed_permissions": sorted(s_set - t_set),
        "common_permissions": sorted(s_set & t_set),
    }


def clone_role(source_role: str, req: RoleCloneModel, current_user: AuthenticatedUser, db: Session):
    base_perms = get_role_permissions(db, current_user.company_id, source_role)
    if base_perms is None:
        raise HTTPException(404, "El rol base no existe.")
    merged = set(base_perms) | set(req.additional_permissions)
    allowed = set(current_user.permissions) - {"platform:manage"}
    if not merged <= allowed or req.role_key == "platform_admin":
        raise HTTPException(403, "No puede conceder permisos superiores a los propios.")
    if role_exists(db, current_user.company_id, req.role_key):
        raise DomainConflictException("El rol ya existe.")
    if role_title_exists(db, current_user.company_id, req.title):
        raise DomainConflictException("Ya existe un rol con ese nombre.")
    crole = CustomRole(
        company_id=current_user.company_id,
        role_key=req.role_key,
        title=req.title,
        description=req.description,
        permissions_json=json.dumps(sorted(merged)),
    )
    db.add(crole)
    db.commit()
    return {"role": req.role_key, "title": req.title, "description": req.description, "permissions": sorted(merged)}


def create_custom_role(req: RoleCreateModel, current_user: AuthenticatedUser, db: Session):
    allowed = set(current_user.permissions) - {"platform:manage"}
    if not set(req.permissions) <= allowed or req.role_key == "platform_admin":
        raise HTTPException(403, "No puede conceder permisos superiores a los propios.")
    if role_exists(db, current_user.company_id, req.role_key):
        raise DomainConflictException("El rol ya existe.")
    if role_title_exists(db, current_user.company_id, req.title):
        raise DomainConflictException("Ya existe un rol con ese nombre.")
    db.add(
        CustomRole(
            company_id=current_user.company_id,
            role_key=req.role_key,
            title=req.title,
            description=req.description,
            permissions_json=json.dumps(sorted(set(req.permissions))),
        )
    )
    db.commit()
    return {
        "role": req.role_key,
        "title": req.title,
        "description": req.description,
        "permissions": sorted(set(req.permissions)),
    }


def custom_role_impact(role_key: str, current_user: AuthenticatedUser, db: Session):
    role = db.scalar(
        select(CustomRole).where(CustomRole.company_id == current_user.company_id, CustomRole.role_key == role_key)
    )
    if not role:
        raise HTTPException(404, "Rol personalizado no encontrado.")
    users = db.scalars(
        select(UserModel).where(UserModel.company_id == current_user.company_id, UserModel.role == role_key)
    ).all()
    return {
        "role": role_key,
        "title": role.title,
        "description": role.description,
        "permissions": sorted(json.loads(role.permissions_json)),
        "role_hash": role_impact_hash(role, users),
        "affected_users": len(users),
        "users": [
            {"name": user.full_name or user.email, "email": user.email, "is_active": user.is_active} for user in users
        ],
    }


def update_custom_role(role_key: str, payload: RoleUpdateModel, current_user: AuthenticatedUser, db: Session):
    db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id).with_for_update())
    role = db.scalar(
        select(CustomRole)
        .where(CustomRole.company_id == current_user.company_id, CustomRole.role_key == role_key)
        .with_for_update()
    )
    if not role:
        raise HTTPException(404, "Solo se pueden editar roles personalizados de esta empresa.")
    if not set(payload.permissions) <= (set(current_user.permissions) - {"platform:manage"}):
        raise HTTPException(403, "No puedes conceder permisos que no posees.")
    if payload.title.strip().casefold() != role.title.strip().casefold() and role_title_exists(
        db, current_user.company_id, payload.title
    ):
        raise DomainConflictException("Ya existe un rol con ese nombre.")
    users = db.scalars(
        select(UserModel).where(UserModel.company_id == current_user.company_id, UserModel.role == role_key)
    ).all()
    if len(users) != payload.affected_users:
        raise DomainConflictException("Los usuarios afectados cambiaron. Revisa nuevamente el impacto.")
    if role_impact_hash(role, users) != payload.expected_role_hash:
        raise DomainConflictException("El rol o sus usuarios cambiaron. Actualice la revisión de impacto antes de guardar.")
    previous = {"title": role.title, "permissions": json.loads(role.permissions_json)}
    role.title = payload.title.strip()
    role.description = payload.description
    role.permissions_json = json.dumps(sorted(set(payload.permissions)))
    for user in users:
        revoke_user_sessions(db, user.id)
    record_audit_event(
        db,
        current_user.company_id,
        current_user.user_id,
        current_user.email,
        "CUSTOM_ROLE_UPDATED",
        "CustomRole",
        role.id,
        diff={"previous": previous, "new": payload.model_dump()},
        reason=payload.reason,
        category="GOVERNANCE",
    )
    db.commit()
    return {
        "role": role.role_key,
        "title": role.title,
        "description": role.description,
        "permissions": json.loads(role.permissions_json),
        "is_custom": True,
    }


def delete_custom_role(
    role_key: str, affected_users: int, replacement_role: Optional[str], current_user: AuthenticatedUser, db: Session
):
    db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id).with_for_update())
    role = db.scalar(
        select(CustomRole)
        .where(CustomRole.company_id == current_user.company_id, CustomRole.role_key == role_key)
        .with_for_update()
    )
    if not role:
        raise HTTPException(404, "Solo se pueden eliminar roles personalizados de esta empresa.")
    users = db.scalars(
        select(UserModel).where(UserModel.company_id == current_user.company_id, UserModel.role == role_key)
    ).all()
    if len(users) != affected_users:
        raise DomainConflictException("Los usuarios afectados cambiaron. Revisa nuevamente el impacto.")
    if users:
        if (
            not replacement_role
            or replacement_role == role_key
            or not role_exists(db, current_user.company_id, replacement_role)
        ):
            raise HTTPException(422, "Selecciona un rol de reemplazo para los usuarios afectados.")
        ensure_role_delegable(db, current_user, replacement_role)
        for user in users:
            user.role = replacement_role
            revoke_user_sessions(db, user.id)
    record_audit_event(
        db,
        current_user.company_id,
        current_user.user_id,
        current_user.email,
        "CUSTOM_ROLE_DELETED",
        "CustomRole",
        role.id,
        diff={"role": role_key, "affected_users": len(users), "replacement_role": replacement_role},
        category="GOVERNANCE",
    )
    db.delete(role)
    db.commit()
    return {"deleted": True, "affected_users": len(users)}
