import secrets
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.seguridad.application.auxiliares.ensure_role_delegable import ensure_role_delegable
from salesia.modules.seguridad.application.auxiliares.get_role_title import get_role_title
from salesia.modules.seguridad.application.auxiliares.mail_challenge import mail_challenge
from salesia.modules.seguridad.application.auxiliares.role_exists import role_exists
from salesia.modules.seguridad.application.contracts.membresias import InvitationRequest, MembershipUpdateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.infrastructure.models import AuthChallenge, AuthMail
from salesia.modules.seguridad.infrastructure.security import hash_password
from salesia.modules.seguridad.infrastructure.sessions import revoke_user_sessions
from salesia.shared.infrastructure.errors import (
    DomainConflictException,
    DomainForbiddenException,
    DomainNotFoundException,
)
from salesia.shared.infrastructure.models import BranchModel, CompanyModel, JobModel, UserModel


def invite_member(req: InvitationRequest, current_user: AuthenticatedUser, db: Session):
    if not role_exists(db, current_user.company_id, req.role):
        raise HTTPException(422, "Rol no permitido.")
    ensure_role_delegable(db, current_user, req.role)
    if req.branch_id is not None:
        branch = db.get(BranchModel, req.branch_id)
        if not branch or branch.company_id != current_user.company_id:
            raise DomainForbiddenException("Sucursal no encontrada o no pertenece a la empresa.")
    email = str(req.email).lower()
    if db.scalar(select(UserModel.id).where(func.lower(UserModel.email) == email)):
        raise DomainConflictException("No se puede crear la invitación para esa dirección.")
    user = UserModel(
        company_id=current_user.company_id,
        email=email,
        hashed_password=hash_password(secrets.token_urlsafe(64)),
        role=req.role,
        is_active=False,
    )
    db.add(user)
    db.flush()
    role_name = get_role_title(db, current_user.company_id, req.role)
    challenge = mail_challenge(db, user, "invitation", current_user.email, role_name)
    record_audit_event(
        db,
        company_id=current_user.company_id,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        action="INVITATION_CREATED",
        entity_type="User",
        entity_id=user.id,
        diff={"email": email, "role": req.role},
        reason="Invitacion de miembro creada",
        category="GOVERNANCE",
        fail_critical=False,
    )
    db.commit()
    return {
        "invitation_id": challenge.id,
        "user_id": user.id,
        "email": email,
        "role": req.role,
        "company_id": current_user.company_id,
        "status": "pending",
    }


def resend_invitation(membership_id: UUID, current_user: AuthenticatedUser, db: Session):
    user = db.scalar(
        select(UserModel)
        .where(UserModel.id == membership_id, UserModel.company_id == current_user.company_id)
        .with_for_update()
    )
    if not user:
        other = db.get(UserModel, membership_id)
        if other and other.company_id != current_user.company_id:
            raise DomainForbiddenException("No tiene permisos para modificar invitaciones de otra empresa.")
        raise DomainNotFoundException("Invitación no encontrada.")
    pending = db.scalar(
        select(AuthChallenge).where(
            AuthChallenge.user_id == user.id, AuthChallenge.purpose == "invitation", AuthChallenge.used_at.is_(None)
        )
    )
    if user.is_active or not pending:
        raise DomainConflictException("La membresía no tiene una invitación pendiente.")
    db.execute(delete(AuthMail).where(AuthMail.recipient == user.email, AuthMail.sent_at.is_(None)))
    role_name = get_role_title(db, current_user.company_id, user.role)
    challenge = mail_challenge(db, user, "invitation", current_user.email, role_name)
    record_audit_event(
        db,
        company_id=current_user.company_id,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        action="INVITATION_RESENT",
        entity_type="User",
        entity_id=user.id,
        diff={"email": user.email, "role": user.role},
        reason="Invitacion de miembro reenviada",
        category="GOVERNANCE",
        fail_critical=False,
    )
    db.commit()
    return {"invitation_id": challenge.id, "user_id": user.id, "email": user.email, "status": "pending"}


def cancel_invitation(membership_id: UUID, current_user: AuthenticatedUser, db: Session):
    user = db.scalar(
        select(UserModel)
        .where(UserModel.id == membership_id, UserModel.company_id == current_user.company_id)
        .with_for_update()
    )
    if not user:
        other = db.get(UserModel, membership_id)
        if other and other.company_id != current_user.company_id:
            raise DomainForbiddenException("No tiene permisos para cancelar invitaciones de otra empresa.")
        raise DomainNotFoundException("Invitación no encontrada.")
    pending = db.scalar(
        select(AuthChallenge).where(
            AuthChallenge.user_id == user.id, AuthChallenge.purpose == "invitation", AuthChallenge.used_at.is_(None)
        )
    )
    if user.is_active or not pending:
        raise DomainConflictException("La membresía no tiene una invitación pendiente.")
    email = user.email
    role = user.role
    db.execute(delete(AuthMail).where(AuthMail.recipient == email, AuthMail.sent_at.is_(None)))
    db.execute(delete(AuthChallenge).where(AuthChallenge.user_id == user.id))
    record_audit_event(
        db,
        company_id=current_user.company_id,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        action="INVITATION_CANCELLED",
        entity_type="User",
        entity_id=user.id,
        diff={"email": email, "role": role},
        reason="Invitacion de miembro cancelada",
        category="GOVERNANCE",
        fail_critical=False,
    )
    db.delete(user)
    db.commit()
    return {"status": "cancelled", "membership_id": membership_id, "email": email}


def update_membership(
    membership_id: UUID, req: MembershipUpdateModel, current_user: AuthenticatedUser, db: Session
):
    db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id).with_for_update())
    user = db.scalar(
        select(UserModel).where(UserModel.id == membership_id, UserModel.company_id == current_user.company_id)
    )
    if not user:
        other = db.get(UserModel, membership_id)
        if other and other.company_id != current_user.company_id:
            raise DomainForbiddenException("No tiene permisos para modificar recursos de otra empresa.")
        raise DomainNotFoundException("Membresía no encontrada.")
    if req.role is not None and not role_exists(db, current_user.company_id, req.role):
        raise HTTPException(422, "Rol no permitido.")
    if req.role is not None:
        ensure_role_delegable(db, current_user, req.role)
    if (
        user.role == "company_admin"
        and user.is_active
        and (req.is_active is False or (req.role is not None and req.role != "company_admin"))
    ):
        admins = db.scalar(
            select(func.count())
            .select_from(UserModel)
            .where(
                UserModel.company_id == current_user.company_id,
                UserModel.role == "company_admin",
                UserModel.is_active.is_(True),
            )
        )
        if admins <= 1:
            raise DomainConflictException("Debe permanecer al menos un administrador activo.")
    previous_role = user.role
    from salesia.modules.seguridad.application.acceso_efectivo import verify_change
    role_impact = verify_change(db, current_user, user, req)
    if req.is_active is False and user.is_active:
        if not req.reason or len(req.reason.strip()) < 5:
            raise HTTPException(422, "Indique el motivo de la baja desde la revisión de responsabilidades.")
        from salesia.modules.seguridad.application.traspaso_usuario import assert_ready, end_operational_access
        assert_ready(db, current_user, user.id)
        end_operational_access(db, current_user, user.id, req.reason)
    if req.role is not None:
        user.role = req.role
    if req.is_active is not None:
        user.is_active = req.is_active
    if req.is_active is False or (req.role is not None and req.role != previous_role):
        db.execute(
            update(JobModel)
            .where(
                JobModel.company_id == current_user.company_id,
                JobModel.requested_by == user.id,
                JobModel.status.in_(["pending", "running"]),
            )
            .values(status="cancelled", cancel_requested=True)
        )
    revoke_user_sessions(db, user.id)
    record_audit_event(
        db,
        company_id=current_user.company_id,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        action="MEMBERSHIP_UPDATED",
        entity_type="User",
        entity_id=user.id,
        diff={"requested": req.model_dump(exclude_unset=True), "role_impact": role_impact},
        reason=req.reason or "Actualizacion de membresia o rol",
        category="GOVERNANCE",
        fail_critical=False,
    )
    db.commit()
    return {"membership_id": user.id, "role": user.role, "is_active": user.is_active}


def transfer_admin(membership_id: UUID, current_user: AuthenticatedUser, db: Session):
    if current_user.role != "company_admin":
        raise HTTPException(403, "Solo el administrador actual puede transferir la administración.")
    if current_user.user_id == membership_id:
        raise DomainConflictException("No puede transferir la administración a sí mismo.")
    target_user = db.scalar(
        select(UserModel).where(UserModel.id == membership_id, UserModel.company_id == current_user.company_id)
    )
    if not target_user:
        other = db.get(UserModel, membership_id)
        if other and other.company_id != current_user.company_id:
            raise DomainForbiddenException("No tiene permisos sobre otra empresa.")
        raise DomainNotFoundException("Usuario destino no encontrado.")
    if not target_user.is_active:
        raise DomainConflictException("El usuario destino debe estar activo para recibir la administración.")
    target_user.role = "company_admin"
    caller = db.get(UserModel, current_user.user_id)
    caller.role = "manager"
    revoke_user_sessions(db, caller.id)
    db.commit()
    return {"status": "transferred", "new_admin_id": str(target_user.id), "previous_admin_id": str(caller.id)}
