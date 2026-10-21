import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.clientes.application.contracts.clientes import ArchiveRestoreModel, CustomerStatusUpdateModel
from salesia.modules.clientes.infrastructure.models import CustomerModel
from salesia.modules.clientes.infrastructure.perfiles import ensure_customer_profile
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainConflictException, DomainNotFoundException
from salesia.shared.infrastructure.models import AuditLogModel


def archive_customer(
    customer_id: UUID, req: Optional[ArchiveRestoreModel], current_user: AuthenticatedUser, db: Session
):
    customer = db.execute(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    ).scalar_one_or_none()
    if not customer:
        raise DomainNotFoundException("Cliente no encontrado.")

    profile = ensure_customer_profile(db, customer)
    if req and req.version is not None and req.version != profile.version:
        raise DomainConflictException("Conflicto de concurrencia al archivar cliente.")

    customer.is_active = False
    profile.status = "archived"
    profile.version += 1

    audit = AuditLogModel(
        id=uuid4(),
        company_id=current_user.company_id,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        action="CUSTOMER_ARCHIVED",
        entity_type="Customer",
        entity_id=customer.id,
        trace_id=str(uuid4()),
        payload_diff=json.dumps({"reason": req.reason if req else "Archivado", "is_active": False}),
    )
    db.add(audit)
    db.commit()

    return {
        "id": str(customer.id),
        "customer_id": str(customer.id),
        "is_active": False,
        "status": "archived",
        "version": profile.version,
        "archived_at": datetime.now(timezone.utc).isoformat(),
    }


def restore_customer(
    customer_id: UUID, req: Optional[ArchiveRestoreModel], current_user: AuthenticatedUser, db: Session
):
    customer = db.execute(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    ).scalar_one_or_none()
    if not customer:
        raise DomainNotFoundException("Cliente no encontrado.")

    profile = ensure_customer_profile(db, customer)
    if req and req.version is not None and req.version != profile.version:
        raise DomainConflictException("Conflicto de concurrencia al restaurar cliente.")

    dup = db.execute(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id,
            CustomerModel.id != customer.id,
            CustomerModel.doc_type == customer.doc_type,
            CustomerModel.doc_number == customer.doc_number,
            CustomerModel.is_active.is_(True),
        )
    ).scalar_one_or_none()
    if dup:
        raise DomainConflictException("No se puede restaurar: existe otro cliente activo con el mismo documento.")

    customer.is_active = True
    profile.status = "active"
    profile.version += 1

    audit = AuditLogModel(
        id=uuid4(),
        company_id=current_user.company_id,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        action="CUSTOMER_RESTORED",
        entity_type="Customer",
        entity_id=customer.id,
        trace_id=str(uuid4()),
        payload_diff=json.dumps({"is_active": True}),
    )
    db.add(audit)
    db.commit()

    return {
        "id": str(customer.id),
        "customer_id": str(customer.id),
        "is_active": True,
        "status": "active",
        "version": profile.version,
        "restored_at": datetime.now(timezone.utc).isoformat(),
    }


def update_customer_status(
    customer_id: UUID, req: CustomerStatusUpdateModel, current_user: AuthenticatedUser, db: Session
):
    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    )
    if not cust:
        raise DomainNotFoundException("Cliente no encontrado.")

    profile = ensure_customer_profile(db, cust)
    profile.status = req.status
    if req.status == "blocked":
        profile.is_credit_blocked = True
        profile.credit_block_reason = req.reason or "Bloqueado administrativamente"
        profile.credit_block_until = req.block_until
    elif req.status == "active":
        profile.is_credit_blocked = False
        profile.credit_block_until = None
        cust.is_active = True
    elif req.status == "archived":
        cust.is_active = False

    profile.version += 1
    db.commit()

    return {
        "customer_id": str(customer_id),
        "status": profile.status,
        "is_active": cust.is_active,
        "is_credit_blocked": profile.is_credit_blocked,
        "version": profile.version,
    }
