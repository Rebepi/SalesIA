import hashlib
import json

from fastapi import HTTPException
from sqlalchemy import select

from salesia.modules.organizacion.application.perfil_operativo import current as operating_profile
from salesia.modules.seguridad.application.auxiliares.ensure_role_delegable import ensure_role_delegable
from salesia.modules.seguridad.domain.roles import Permission, get_role_catalog
from salesia.modules.seguridad.infrastructure.models import CustomRole
from salesia.shared.infrastructure.models import UserModel

SENSITIVE = {"products:cost:read", "users:manage", "organization:manage", "approvals:manage", "cash:register:manage", "audit:logs:export", "reports:export", "payments:write", "sales:cancel"}


def role_source(db, company_id, key):
    built_in = next((row for row in get_role_catalog() if row.role.value == key), None)
    if built_in:
        return {"kind": "built_in", "key": key, "title": built_in.title, "permissions": sorted(built_in.permissions)}
    row = db.scalar(select(CustomRole).where(CustomRole.company_id == company_id, CustomRole.role_key == key))
    if row is None:
        raise HTTPException(404, "Rol no encontrado en la empresa activa.")
    return {"kind": "custom", "key": key, "title": row.title, "permissions": sorted(json.loads(row.permissions_json))}


def member_access(db, user, identifier, proposed_role=None):
    row = db.scalar(select(UserModel).where(UserModel.company_id == user.company_id, UserModel.id == identifier))
    if row is None:
        raise HTTPException(404, "Usuario no encontrado en la empresa activa.")
    source = role_source(db, user.company_id, row.role)
    target = role_source(db, user.company_id, proposed_role or row.role)
    delegable = not (target["key"] == "company_admin" and user.role != "company_admin") and set(target["permissions"]).issubset(set(user.permissions))
    current_permissions, target_permissions = set(source["permissions"]), set(target["permissions"])
    added, removed = sorted(target_permissions - current_permissions), sorted(current_permissions - target_permissions)
    profile = operating_profile(db, user.company_id)
    from salesia.modules.seguridad.application.traspaso_usuario import preflight
    responsibilities = preflight(db, user, identifier)
    risks = [{"key": group["key"], "label": group["label"], "count": group["count"], "missing_permissions": sorted(set(group["required_permissions"]) - target_permissions)} for group in responsibilities["groups"] if group["count"] and set(group["required_permissions"]) - target_permissions]
    definition = "Los permisos proceden del rol vigente de la empresa. Una cuenta suspendida no puede operar. Cada operación vuelve a evaluar el documento, el perfil del negocio, el período, la revisión independiente y su alcance de datos; disponer del permiso no omite esas condiciones. Las delegaciones de aprobación representan a otra persona y no conceden sus permisos generales."
    result = {"user_id": str(row.id), "name": row.full_name or row.email, "email": row.email, "is_active": row.is_active, "source": source, "target": target, "can_assign_target": delegable, "added": added, "removed": removed, "sensitive_added": sorted(set(added) & SENSITIVE), "responsibilities_at_risk": risks, "cost_visibility": {"current": "products:cost:read" in current_permissions and row.is_active, "proposed": "products:cost:read" in target_permissions and row.is_active, "required_permission": "products:cost:read"}, "operating_profile": {"version": profile["version"], "profile": profile["profile"], "enabled": profile["enabled"]}, "permissions": [{"permission": permission.value, "granted_by_role": permission.value in current_permissions, "effective_for_active_account": row.is_active and permission.value in current_permissions, "proposed_grant": permission.value in target_permissions, "sensitive": permission.value in SENSITIVE, "explanation": f"Concedido por el rol {source['title']}." if permission.value in current_permissions and row.is_active else "La cuenta está suspendida; el permiso del rol no habilita operaciones." if permission.value in current_permissions else f"El rol {source['title']} no incluye este permiso."} for permission in Permission if permission.value != "platform:manage"], "definition": definition, "effects": ["Las sesiones de la persona se revocan al modificar su rol.", "Los documentos conservan sus autores y aprobaciones anteriores.", "Los nuevos permisos se comprueban al iniciar una nueva sesión."]}
    signature = {"result": result, "member_updated_at": row.updated_at.isoformat(), "responsibility_hash": responsibilities["preview_hash"]}
    result["access_hash"] = hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()
    return result


def verify_change(db, user, member, payload):
    if payload.role is None or payload.role == member.role:
        return None
    ensure_role_delegable(db, user, payload.role)
    if not payload.reason or len(payload.reason.strip()) < 5:
        raise HTTPException(422, "Indique el motivo del cambio de rol después de revisar su impacto.")
    impact = member_access(db, user, member.id, payload.role)
    if not payload.access_hash or payload.access_hash != impact["access_hash"]:
        raise HTTPException(409, "Revise los permisos efectivos y el impacto actual antes de cambiar el rol.")
    if impact["responsibilities_at_risk"] and not payload.acknowledge_responsibilities:
        raise HTTPException(409, "El nuevo rol deja responsabilidades sin permisos suficientes. Traspáselas o reconozca explícitamente este efecto antes de guardar.")
    return {key: impact[key] for key in ("access_hash", "source", "target", "added", "removed", "sensitive_added", "responsibilities_at_risk", "cost_visibility")}
